#!/bin/bash
#
# Author: Pablo de Andres<mailto:pablo.de.andres@iwm.fraunhofer.de>
#         Material Informatics Team, Fraunhofer IWM
#
# Description: This script install the LAMMPS engine and its Python binding
#              Used as part of the installation for the Simlammps wrapper.
#
# Run Information: This script is run manually.

###################################
### Install engine requirements ###
###################################
./install_engine_requirements.sh

################################
### Download necessary files ###
################################
echo "Checking out a recent stable version"
git clone -b stable https://github.com/lammps/lammps.git
cd lammps

############################
### Perform installation ###
############################
mkdir build
cd  build

# MPI, PNG, Jpeg, FFMPEG are auto-detected
cmake ../cmake -DPKG_MOLECULE=yes -DLAMMPS_EXCEPTIONS=yes -DBUILD_LIB=yes -DBUILD_SHARED_LIBS=yes
echo "Building LAMMPS shared library"
make
echo "Installing LAMMPS shared library and python package"
make install-python

#########################
### Test installation ###
#########################
{
    echo "Checker whether LAMMPS is available in python"
    python3 -c 'from lammps import PyLammps as p;p().command("print \"Hi from PyLammps\"")' &&
    echo "LAMMPS installation complete." &&
    # Clean-up
    read -p "Do you want to remove the LAMMPS folder? [y/N] " -n 1 -r &&
    echo &&
    if [[ $REPLY =~ ^[Yy]$ ]]
    then
        echo "Cleaning up LAMMPS folder..."
        cd ../..
        rm -rf lammps
        echo "Done!"
    else
        echo "Folder was not removed."
    fi
} || {
    echo "There was an error with the installation."
    echo "Please, try again or contact the developer."
}
