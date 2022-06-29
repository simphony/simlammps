FROM python:3.9
LABEL maintainer="simphony@fraunhofer.iwm.de"

# Install requirements
RUN apt-get update && \
    apt-get install -y git g++ wget cmake \
    libjpeg-dev libpng-dev ffmpeg fftw3 fftw3-dev pkg-config

# Install LAMMPS
WORKDIR /lammps
RUN git clone -b stable https://github.com/lammps/lammps.git .
WORKDIR /lammps/build
RUN cmake  -C ../cmake/presets/basic.cmake -D BUILD_SHARED_LIBS=on -D LAMMPS_EXCEPTIONS=on -D PKG_PYTHON=on ../cmake && \
    cmake --build . && \
    cmake --install .

# Install osp-core
RUN pip install simphony-osp

# Install simlammps
WORKDIR /simphony/wrappers/simlammps
ADD . .
RUN pip install .
RUN pico install simlammps.ontology.yml

# NOTE: This env variable should theoretically be automatically set
ENV LD_LIBRARY_PATH=/lammps/build

# docker build -t simphony/simlammps .
# docker run -ti --rm --entrypoint=/bin/bash simphony/simlammps
