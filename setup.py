from setuptools import find_packages, setup

from packageinfo import NAME, OSP_CORE_MAX, OSP_CORE_MIN, VERSION

# Read description
with open("README.md") as readme:
    README_TEXT = readme.read()


# main setup configuration class
setup(
    name=NAME,
    version=VERSION,
    author="Material Informatics Team, Fraunhofer IWM.",
    url="www.simphony-project.eu",
    description="The lammps wrapper for SimPhoNy",
    keywords="simphony, cuds, Fraunhofer IWM, lammps",
    long_description=README_TEXT,
    install_requires=[
        "osp-core>=" + OSP_CORE_MIN + ", <" + OSP_CORE_MAX,
    ],
    tests_require=[
        "unittest2",
    ],
    packages=find_packages(exclude=("examples", "tests")),
    test_suite="tests",
    entry_points={"wrappers": "simlammps = osp.wrappers.simlammps:SimlammpsSession"},
)
