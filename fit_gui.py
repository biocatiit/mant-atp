import sys
import numpy as np
import pandas as pd
from lmfit import Model

from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, QHBoxLayout,
                               QPushButton, QFileDialog, QMessageBox, QCheckBox, QRadioButton,
                               QButtonGroup, QLabel)
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure
from matplotlib.widgets import SpanSelector


def model_func(t, P1, T1, P2, T2):
    # I = 1 − P1(1 − e−t/T1) − P2(1 − e−t/T2)
    return 1 - P1 * (1 - np.exp(-t / T1)) - P2 * (1 - np.exp(-t / T2))


class Win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XLSX plot + lmfit (double exp) — minimal")
        self.resize(900, 600)

        self.df = None
        self.trim_mask = None  # Boolean mask: True = keep, False = trimmed
        self.fit_result = None  # Store last fit result
        self.current_fit_mode = None  # 'data' or 'subtraction'
        self.selected_span = None  # (tmin, tmax) of selected region

        w = QWidget()
        self.setCentralWidget(w)
        lay = QVBoxLayout(w)

        # Open button
        self.btn_open = QPushButton("Open XLSX")
        lay.addWidget(self.btn_open)

        # Fit options: two mutually exclusive radio buttons
        fit_layout = QHBoxLayout()
        fit_layout.addWidget(QLabel("Fit:"))
        self.rb_fit_data = QRadioButton("fit data")
        self.rb_fit_sub = QRadioButton("fit subtraction")
        self.rb_fit_sub.setChecked(True)  # default
        self.fit_group = QButtonGroup(self)
        self.fit_group.addButton(self.rb_fit_data)
        self.fit_group.addButton(self.rb_fit_sub)
        fit_layout.addWidget(self.rb_fit_data)
        fit_layout.addWidget(self.rb_fit_sub)
        self.btn_fit = QPushButton("Run Fit")
        fit_layout.addWidget(self.btn_fit)
        fit_layout.addStretch()
        lay.addLayout(fit_layout)

        # Checkboxes for plot options
        cb_layout = QHBoxLayout()
        self.cb_data = QCheckBox("plot data")
        self.cb_bg = QCheckBox("plot background")
        self.cb_sub = QCheckBox("plot subtraction")
        self.cb_sub.setChecked(True)  # default selected
        cb_layout.addWidget(self.cb_data)
        cb_layout.addWidget(self.cb_bg)
        cb_layout.addWidget(self.cb_sub)
        cb_layout.addStretch()
        lay.addLayout(cb_layout)

        # Trim controls
        trim_layout = QHBoxLayout()
        trim_layout.addWidget(QLabel("Trim: drag on plot to select region, then click Delete"))
        self.btn_delete = QPushButton("Delete Selected")
        self.btn_delete.setEnabled(False)
        self.btn_reset_trim = QPushButton("Reset Trim")
        trim_layout.addWidget(self.btn_delete)
        trim_layout.addWidget(self.btn_reset_trim)
        trim_layout.addStretch()
        lay.addLayout(trim_layout)

        # Matplotlib canvas
        self.fig = Figure(constrained_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = Canvas(self.fig)
        lay.addWidget(self.canvas, 1)

        # SpanSelector for trim
        self.span_selector = SpanSelector(
            self.ax, self.on_span_select, 'horizontal',
            useblit=True,
            props=dict(alpha=0.3, facecolor='red'),
            interactive=True,
            drag_from_anywhere=True
        )

        # Connect signals
        self.btn_open.clicked.connect(self.open_xlsx)
        self.btn_fit.clicked.connect(self.fit_and_plot)
        self.cb_data.stateChanged.connect(self.replot)
        self.cb_bg.stateChanged.connect(self.replot)
        self.cb_sub.stateChanged.connect(self.replot)
        self.btn_delete.clicked.connect(self.delete_selected)
        self.btn_reset_trim.clicked.connect(self.reset_trim)

    def open_xlsx(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Excel", "", "Excel (*.xlsx *.xls)")
        if not path:
            return
        try:
            self.df = pd.read_excel(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return

        # Reset state
        n = len(self.df)
        self.trim_mask = np.ones(n, dtype=bool)
        self.fit_result = None
        self.current_fit_mode = None
        self.selected_span = None
        self.btn_delete.setEnabled(False)

        self.setWindowTitle(f"Loaded: {path}")

        # Auto fit subtraction after loading
        self.rb_fit_sub.setChecked(True)
        self.fit_and_plot()

    def get_data(self):
        """Get time, data, background arrays with trim mask applied."""
        if self.df is None:
            return None, None, None

        try:
            t = self.df["Time [ms]"].to_numpy(dtype=float)
            data = self.df["Data_"].to_numpy(dtype=float)
            bg = self.df["Background"].to_numpy(dtype=float)
        except Exception as e:
            QMessageBox.critical(self, "Missing columns",
                                 "Need columns: Time [ms], Data_, Background\n\n" + str(e))
            return None, None, None

        # Apply trim mask
        mask = self.trim_mask & np.isfinite(t) & np.isfinite(data) & np.isfinite(bg)
        return t[mask], data[mask], bg[mask]

    def on_span_select(self, tmin, tmax):
        """Called when user selects a span on the plot."""
        self.selected_span = (tmin, tmax)
        self.btn_delete.setEnabled(True)

    def delete_selected(self):
        """Delete the selected time region from data."""
        if self.selected_span is None or self.df is None:
            return

        tmin, tmax = self.selected_span
        t_full = self.df["Time [ms]"].to_numpy(dtype=float)

        # Mark points in the selected range as trimmed
        in_range = (t_full >= tmin) & (t_full <= tmax)
        self.trim_mask = self.trim_mask & ~in_range

        # Clear selection
        self.selected_span = None
        self.btn_delete.setEnabled(False)

        # Replot and refit if needed
        if self.fit_result is not None:
            self.fit_and_plot()
        else:
            self.replot()

    def reset_trim(self):
        """Reset trim mask to include all data."""
        if self.df is None:
            return

        self.trim_mask = np.ones(len(self.df), dtype=bool)
        self.selected_span = None
        self.btn_delete.setEnabled(False)

        # Replot and refit if needed
        if self.fit_result is not None:
            self.fit_and_plot()
        else:
            self.replot()

    def replot(self):
        """Replot based on current state (raw data and/or fit)."""
        if self.df is None:
            return

        t, data, bg = self.get_data()
        if t is None or data is None or bg is None:
            return

        self.ax.cla()

        # Plot raw data based on checkboxes
        if self.cb_data.isChecked():
            self.ax.plot(t, data, "o", label="data", alpha=0.7, markersize=4)
        if self.cb_bg.isChecked():
            self.ax.plot(t, bg, "s", label="background", alpha=0.7, markersize=4)
        if self.cb_sub.isChecked():
            sub = data - bg
            self.ax.plot(t, sub, "^", label="subtraction", alpha=0.7, markersize=4)

        # If we have a fit result, plot the fit curve
        if self.fit_result is not None:
            self._plot_fit_curve(t, data, bg)

        self.ax.set_xlabel("Time [ms]")
        self.ax.set_ylabel("Intensity")
        self.ax.grid(True)
        self.ax.legend()
        self.canvas.draw()

    def _plot_fit_curve(self, t: np.ndarray, data: np.ndarray, bg: np.ndarray):
        """Plot the fit curve on top of data."""
        if self.fit_result is None:
            return

        P1, T1, P2, T2 = (self.fit_result.params[k].value for k in ("P1", "T1", "P2", "T2"))

        # Sort for plotting
        o = np.argsort(t)
        t_sorted = t[o]

        # Generate smooth fit curve
        t_fine = np.linspace(t_sorted.min(), t_sorted.max(), 200)
        y_fit_fine = model_func(t_fine, P1, T1, P2, T2)

        # Scale back to original data scale
        if self.current_fit_mode == 'subtraction':
            y_for_fit = (data - bg)[o]
        else:
            y_for_fit = data[o]

        y_max = np.max(y_for_fit)
        y_fit_scaled = y_fit_fine * y_max

        self.ax.plot(t_fine, y_fit_scaled, "-", color="red", linewidth=2, label="fit")
        self.ax.set_title(f"P1={P1:.3g}, T1={T1:.3g} ms, P2={P2:.3g}, T2={T2:.3g} ms")

    def fit_and_plot(self):
        if self.df is None:
            QMessageBox.warning(self, "No data", "Open an XLSX first.")
            return

        t, data, bg = self.get_data()
        if t is None or data is None or bg is None:
            return

        if len(t) < 6:
            QMessageBox.warning(self, "Too few points", "Need at least ~6 points.")
            return

        # Determine what to fit based on radio button
        if self.rb_fit_data.isChecked():
            y = data
            self.current_fit_mode = 'data'
        else:
            y = data - bg
            self.current_fit_mode = 'subtraction'

        # Sort + normalize (so I(0)~1)
        o = np.argsort(t)
        t_sorted, y_sorted = t[o], y[o]
        y_norm = y_sorted / np.max(y_sorted)

        g = Model(model_func)
        p = g.make_params(P1=0.5, T1=max(1.0, float(np.median(t_sorted))),
                          P2=0.3, T2=max(10.0, float(np.max(t_sorted))))
        p["P1"].min = 0; p["P1"].max = 1
        p["P2"].min = 0; p["P2"].max = 1
        p["T1"].min = 1e-12
        p["T2"].min = 1e-12

        self.fit_result = g.fit(y_norm, p, t=t_sorted)

        # Replot with fit
        self.replot()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Win()
    win.show()
    sys.exit(app.exec())
