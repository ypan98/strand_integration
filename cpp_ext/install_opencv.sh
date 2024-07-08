#!/bin/bash

# Exit immediately if a command exits with a non-zero status
set -e

# Define OpenCV version
OPENCV_VERSION="4.5.5"

# Define installation directory
INSTALL_DIR="."

# Clone OpenCV and OpenCV contrib repositories
echo "Cloning OpenCV repositories..."
git clone --branch ${OPENCV_VERSION} https://github.com/opencv/opencv.git
git clone --branch ${OPENCV_VERSION} https://github.com/opencv/opencv_contrib.git

# Create build directory
echo "Creating build directory..."
mkdir -p opencv/build
cd opencv/build

# Configure the build with CMake
echo "Configuring the build with CMake..."
cmake -D CMAKE_BUILD_TYPE=Release \
      -D CMAKE_INSTALL_PREFIX=${INSTALL_DIR} \
      -D OPENCV_EXTRA_MODULES_PATH=../../opencv_contrib/modules ..

# Build OpenCV
echo "Building OpenCV..."
make -j$(nproc)

# Install OpenCV
echo "Installing OpenCV to ${INSTALL_DIR}..."
make install

# Set up environment variables
echo "Setting up environment variables..."
echo "export OpenCV_DIR=${INSTALL_DIR}/share/opencv4" >> ~/.bashrc
echo "export LD_LIBRARY_PATH=${INSTALL_DIR}/lib:\$LD_LIBRARY_PATH" >> ~/.bashrc
echo "export PKG_CONFIG_PATH=${INSTALL_DIR}/lib/pkgconfig:\$PKG_CONFIG_PATH" >> ~/.bashrc

# Source the updated .bashrc to apply changes immediately
echo "Applying changes..."
source ~/.bashrc

echo "OpenCV ${OPENCV_VERSION} installation complete."

