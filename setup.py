"""Install SimLAMMPS."""

from setuptools import find_packages, setup

# Read description
with open("README.md") as readme:
    README_TEXT = readme.read()

NAME = "simphony-osp-simlammps"
VERSION = "4.0.0"

# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    description="LAMMPS wrapper for SimPhoNy",
    long_description=README_TEXT,
    long_description_content_type="text/markdown",
    url="https://github.com/simphony/simlammps",
    author="Material Informatics Team, Fraunhofer IWM",
    author_email="simphony@iwm.fraunhofer.de",
    maintainer="Material Informatics Team, Fraunhofer IWM",
    maintainer_email="simphony@iwm.fraunhofer.de",
    license="GPLv2",
    platforms=["any"],
    classifiers=[
        "Development Status :: 3 - Alpha",
        "Intended Audience :: Science/Research",
        "Topic :: Scientific/Engineering",
        "Topic :: Scientific/Engineering :: Physics",
        "License :: OSI Approved :: GNU General Public License v2 (GPLv2)",
        "Programming Language :: Python",
        "Programming Language :: Python :: 3 :: Only",
        "Programming Language :: Python :: 3.7",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Operating System :: Microsoft :: Windows",
        "Operating System :: MacOS",
        "Operating System :: Unix",
    ],
    keywords="simphony, Fraunhofer IWM, LAMMPS, wrapper, simulation,"
             "molecular dynamics",
    download_url="https://pypi.org/project/simphony-osp-simlammps/4.0.0/"
                 "#files",
    project_urls={
        "Tracker": "https://github.com/simphony/simlammps/issues",
        "Source": "https://github.com/simphony/simlammps/tree/v4.0.0",
    },
    packages=find_packages(exclude=("examples", "tests")),
    install_requires=[
        "simphony-osp >= 4.0.0rc3, < 5.0.0rc0",
        "numpy",
    ],
    tests_require=[
    ],
    python_requires=">=3.7",
    test_suite="tests",
    entry_points={
        "simphony_osp.wrappers": {
            "SimLAMMPS = simphony_osp_simlammps.wrapper:SimLAMMPS",
        },
    },
)
