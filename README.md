# Simlammps
[![pipeline status](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/simlammps/badges/master/pipeline.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/simlammps/commits/master)
[![coverage report](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/simlammps/badges/master/coverage.svg)](https://gitlab.cc-asp.fraunhofer.de/simphony/wrappers/simlammps/commits/master)

Wrapper for LAMMPS developed by the SimPhoNy group at Fraunhofer IWM

Copyright (c) 2014-2019, Adham Hashibon and Materials Informatics Team at Fraunhofer IWM.
All rights reserved.
Redistribution and use are limited to the scope agreed with the end user.
No parts of this software may be used outside of this context.
No redistribution is allowed without explicit written permission.

Contact: [Pablo de Andres](mailto:pablo.de.andres@iwm.fraunhofer.de)

## Requirements

The SimLammps wrapper is built on top of the [OSP core](https://github.com/simphony/osp-core) package.
The following table describes the version compatibility between these two packages.

|__SimLammps__|__OSP core__|
|:-----------:|:----------:|
|    3.4.x    | 3.5.x-beta |
|    3.3.x    | 3.3.4-beta |
|    3.2.x    | 3.3.0-beta |
|    3.1.x    | 3.2.x-beta |
|    3.0.x    | 3.1.x-beta |
|    2.0.0    |    2.0.x   |
|    0.0.1    |    1.x.x   |

The releases of OSP core are available [here](https://github.com/simphony/osp-core/releases).

## Installation
If LAMMPS is not installed in the system, you can install it by running in your console:
```
    ./install_engine
```

If osp-core is not in the system, install it before:
```
    pip install git+https://github.com/simphony/osp-core.git
```

__NOTE:__ Until a proper, stable version of the ontology with all the entities is available in OSP Core, a toy ontology for temporary usage is provided.
```
    # to install the simlammps ontology
    pico install simlammps/simlammps.ontology.yml
```

The package requires python 3 (tested for 3.7), installation is based on `setuptools`:
```
    # build and install simlammps
    pip install .
```

## Documentation
All information about SimPhoNy and its wrappers is available in the [SimPhoNy docs](https://simphony.readthedocs.io)

The LAMMPS engine documentation can be visited [here](https://lammps.sandia.gov/).

## Directory structure
- osp/wrappers/simlammps -- simlammps wrapper files.
- tests -- unittesting of the code.
- examples -- examples of usage.

## Docker
We have prepared a Dockerfile with all the necessary requirements.
Since osp-core is not public yet, a username and password are necessary to clone it.
This is all simplified via a script called `docker_install.sh`
```shell
    # Build it
    docker build -t simphony/simlammps .
    # Run it (console entypoint)
    docker run -ti --rm --entrypoint=/bin/bash simphony/simlammps
```
