#!/bin/bash
#
# Author: Pablo de Andres<mailto:pablo.de.andres@iwm.fraunhofer.de>
#         Material Informatics Team, Fraunhofer IWM
#
# Description: This script install the requirements for the LAMMPS engine
#              Used as part of the installation for the Simlammps wrapper.
#
# Run Information: This script is called by install_engine.sh

echo "Installing necessary requirements for the engine"
platform=$(python3 -mplatform)

case $platform in
  *"Ubuntu"*)
    sudo apt-get update
    sudo apt-get install build-essential
    sudo apt-get install cmake
    sudo apt-get install libjpeg-dev
    sudo apt-get install libpng-dev
    sudo apt-get install ffmpeg
  ;;
  *"centos"*)
    sudo yum update
    sudo yum install make -y
    sudo yum install cmake -y
    sudo yum install libjpeg -y
    sudo yum install libpng -y
    # install ffmpeg
    git clone https://git.ffmpeg.org/ffmpeg.git ffmpeg
    cd ffmpeg
    ./configure --disable-x86asm
    make
    sudo make install
    rm -rf ffmpeg
  ;;
  # Add other platforms here
esac
