# SimLAMMPS

SimLAMMPS is a SimPhoNy wrapper that enables the use of the LAMMPS molecular 
dynamics simulation engine on the SimPhoNy Open Simulation Platform.

**Disclaimer**: We are **not** affiliated nor associated with the 
[authors of LAMMPS](https://docs.lammps.org/Intro_authors.html).

## Installation

This wrapper requires a working LAMMPS installation. If you are running
Ubuntu or CentOS, you are lucky, as we have prepared a
script that can install it for you.
```
    ./install_engine.sh
```

If you are running a different distribution or operating system, you will
have to install it yourself. Please make sure that LAMMPS is installed before 
proceeding.

The next step is to install the wrapper itself. SimLAMMPS is available on PyPI,
so it can be installed using the
[`pip` package manager](https://pip.pypa.io/en/stable/), you can do so by 
running:

```shell
    pip install simphony-osp-simlammps
```

Finally, the wrapper requires a specific ontology to operate. Download the 
[ontology file](https://github.com/simphony/simlammps/blob/v4.0.0/simphony_osp_simlammps/simlammps.ttl)
and 
[ontology package](https://github.com/simphony/simlammps/blob/v4.0.0/simphony_osp_simlammps/simlammps.yml),
then install the latter with the following command:

```
    pico install simlammps.yml
```

**Note:** The provided ontology is not connected to any 
top-level ontology, therefore its scope is limited to this wrapper. 

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

All information about SimPhoNy is available on the
[SimPhoNy documentation](https://simphony.readthedocs.io/en/v4.0.0rc3). Check out the
[examples folder](https://github.com/simphony/simlammps/blob/v4.0.0/examples)
for examples on how to use SimLAMMPS itself.

The LAMMPS engine documentation is available [here](https://lammps.sandia.gov/).

## License

Copyright (c) 2014-2022, Fraunhofer-Gesellschaft zur Förderung der angewandten
Forschung e.V. acting on behalf of its Fraunhofer IWM.

SimLAMMPS is distributed under the terms of the
[GNU Public License Version 2](https://github.com/simphony/simlammps/blob/v4.0.0/LICENSE)
as required 
[by the license terms of LAMMPS itself](https://docs.lammps.org/Intro_opensource.html).

Contact: [SimPhoNy](mailto:simphony@iwm.fraunhofer.de)
