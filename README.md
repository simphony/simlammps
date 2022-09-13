# SimLAMMPS

SimPhoNy Wrapper for LAMMPS developed by the Materials Informatics team at
Fraunhofer IWM.

Copyright (c) 2014-2022, Adham Hashibon and Materials Informatics Team at
Fraunhofer IWM.
All rights reserved.
Redistribution and use are limited to the scope agreed with the end user.
No parts of this software may be used outside of this context.
No redistribution is allowed without explicit written permission.

Contact: [SimPhoNy](mailto:simphony@iwm.fraunhofer.de@iwm.fraunhofer.de)

## Installation

This wrapper requires a working LAMMPS installation. If you are running
Ubuntu or CentOS, you are lucky, as we have prepared a
script that can install it for you.
```
    ./install_engine.sh
```

If you are running a different distribution or operating system, you will
have to install it yourself. Please make sure that LAMMPS is installed before proceeding.

The next step is to install the wrapper itself, you can do so by running:

```
    # build and install simlammps
    pip install .
```

This will also automatically pull and install the `simphony-osp` package
from PyPI if necessary.

Finally, the wrapper requires an ontology to represent the entities with
which it operates. Install it with the following command:

```
    # to install the simlammps ontology
    pico install simphony_osp_simlammps/simlammps.yml
```

__NOTE:__ Until a proper, stable version of the ontology with all the entities
is available, a toy ontology for temporary usage is provided.

### Docker

Alternatively, you can run the wrapper from a Docker image. We have
prepared a Dockerfile with all the necessary requirements.
```shell
    # Build it
    docker build -t simphony/simlammps .
    # Run it (console entrypoint)
    docker run -ti --rm --entrypoint=/bin/bash simphony/simlammps
```


## Documentation
All information about SimPhoNy and its wrappers is available on the
[SimPhoNy docs](https://simphony.readthedocs.io).

The LAMMPS engine documentation can be visited [here](https://lammps.sandia.gov/).
