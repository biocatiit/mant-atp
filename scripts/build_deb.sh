#!/bin/bash
# Build .deb package for Mant-ATP using fpm

set -e

APP_NAME="mant-atp"
VERSION="1.0.0"
MAINTAINER="Mant-ATP Team <maintainer@example.com>"
DESCRIPTION="GUI application for XLSX data fitting with double exponential model"
ARCH="amd64"

# Paths
DIST_DIR="dist"
BINARY_PATH="${DIST_DIR}/Mant-ATP"
DEB_OUTPUT="${DIST_DIR}/${APP_NAME}_${VERSION}_${ARCH}.deb"

# Verify the binary exists
if [ ! -f "$BINARY_PATH" ]; then
    echo "Error: Binary not found at $BINARY_PATH"
    echo "Run PyInstaller first: pyinstaller Mant-ATP.spec"
    exit 1
fi

# Create temporary directory structure for the package
PACKAGE_ROOT=$(mktemp -d)
trap "rm -rf $PACKAGE_ROOT" EXIT

# Create directory structure
mkdir -p "${PACKAGE_ROOT}/usr/bin"
mkdir -p "${PACKAGE_ROOT}/usr/share/applications"
mkdir -p "${PACKAGE_ROOT}/usr/share/icons/hicolor/256x256/apps"

# Copy binary
cp "$BINARY_PATH" "${PACKAGE_ROOT}/usr/bin/${APP_NAME}"
chmod +x "${PACKAGE_ROOT}/usr/bin/${APP_NAME}"

# Create .desktop file for application menu
cat > "${PACKAGE_ROOT}/usr/share/applications/${APP_NAME}.desktop" << EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Mant-ATP
Comment=XLSX data fitting with double exponential model
Exec=${APP_NAME}
Icon=${APP_NAME}
Terminal=false
Categories=Science;DataVisualization;Qt;
Keywords=xlsx;fitting;plot;data;
EOF

# Build .deb package using fpm
fpm \
    --input-type dir \
    --output-type deb \
    --name "$APP_NAME" \
    --version "$VERSION" \
    --architecture "$ARCH" \
    --maintainer "$MAINTAINER" \
    --description "$DESCRIPTION" \
    --url "https://github.com/yourusername/Mant_ATP" \
    --license "MIT" \
    --depends "libxcb1" \
    --depends "libxkbcommon0" \
    --depends "libgl1" \
    --depends "libfontconfig1" \
    --category "science" \
    --deb-priority "optional" \
    --force \
    --package "$DEB_OUTPUT" \
    --chdir "$PACKAGE_ROOT" \
    .

echo ""
echo "Successfully created: $DEB_OUTPUT"
echo ""
echo "To install: sudo dpkg -i $DEB_OUTPUT"
echo "To remove:  sudo apt remove $APP_NAME"
