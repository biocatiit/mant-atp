import sys
import numpy as np
import pandas as pd
from lmfit import Model

from PySide6.QtWidgets import QApplication, QMainWindow, QWidget, QVBoxLayout, QPushButton, QFileDialog, QMessageBox
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg as Canvas
from matplotlib.figure import Figure


def model_func(t, P1, T1, P2, T2):
    # I = 1 − P1(1 − e−t/T1) − P2(1 − e−t/T2)
    return 1 - P1 * (1 - np.exp(-t / T1)) - P2 * (1 - np.exp(-t / T2))


class Win(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("XLSX plot + lmfit (double exp) — minimal")
        self.resize(900, 600)

        self.df = None

        w = QWidget()
        self.setCentralWidget(w)
        lay = QVBoxLayout(w)

        self.btn_open = QPushButton("Open XLSX")
        self.btn_fit = QPushButton("Fit (and plot)")
        lay.addWidget(self.btn_open)
        lay.addWidget(self.btn_fit)

        self.fig = Figure(constrained_layout=True)
        self.ax = self.fig.add_subplot(111)
        self.canvas = Canvas(self.fig)
        lay.addWidget(self.canvas, 1)

        self.btn_open.clicked.connect(self.open_xlsx)
        self.btn_fit.clicked.connect(self.fit_and_plot)

    def open_xlsx(self):
        path, _ = QFileDialog.getOpenFileName(self, "Open Excel", "", "Excel (*.xlsx *.xls)")
        if not path:
            return
        try:
            self.df = pd.read_excel(path)
        except Exception as e:
            QMessageBox.critical(self, "Error", str(e))
            return
        self.setWindowTitle(f"Loaded: {path}")

    def fit_and_plot(self):
        if self.df is None:
            QMessageBox.warning(self, "No data", "Open an XLSX first.")
            return

        # Fixed columns (minimal version)
        try:
            t = self.df["Time [ms]"].to_numpy(dtype=float)
            y = (self.df["Data_"] - self.df["Background"]).to_numpy(dtype=float)
        except Exception as e:
            QMessageBox.critical(self, "Missing columns",
                                 "Need columns: Time [ms], Data_, Background\n\n" + str(e))
            return

        mask = np.isfinite(t) & np.isfinite(y)
        t, y = t[mask], y[mask]
        if len(t) < 6:
            QMessageBox.warning(self, "Too few points", "Need at least ~6 points.")
            return

        # sort + normalize (so I(0)~1)
        o = np.argsort(t)
        t, y = t[o], y[o]
        y = y / np.max(y)

        g = Model(model_func)
        p = g.make_params(P1=0.5, T1=max(1.0, float(np.median(t))), P2=0.3, T2=max(10.0, float(np.max(t))))
        p["P1"].min = 0; p["P1"].max = 1
        p["P2"].min = 0; p["P2"].max = 1
        p["T1"].min = 1e-12
        p["T2"].min = 1e-12

        try:
            r = g.fit(y, p, t=t)
        except Exception as e:
            QMessageBox.critical(self, "Fit failed", str(e))
            return

        yfit = r.best_fit
        P1, T1, P2, T2 = (r.params[k].value for k in ("P1", "T1", "P2", "T2"))

        self.ax.cla()
        self.ax.plot(t, y, "o", label="data")
        self.ax.plot(t, yfit, "-", label="fit")
        self.ax.grid(True)
        self.ax.legend()

        self.ax.set_title(f"P1={P1:.3g}, T1={T1:.3g} ms, P2={P2:.3g}, T2={T2:.3g} ms")
        self.canvas.draw()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    win = Win()
    win.show()
    sys.exit(app.exec())
