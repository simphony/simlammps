"""Creates a simple run for testing the wrapper"""

import os

import unittest2 as unittest
from osp.core.namespaces import simlammps_ontology

from osp.wrappers.simlammps import SimlammpsSession


@unittest.skipIf(
    os.environ.get("CI_RUNNING"),
    "Lammps cannot capture the stdout/stderr streams from the CI",
)
class TestSimple(unittest.TestCase):
    def setUp(self):
        sess = SimlammpsSession()
        self.lammps_wrapper = simlammps_ontology.SimlammpsWrapper(session=sess)

        # define a material:
        mass = simlammps_ontology.Mass(value=0.2)
        material = simlammps_ontology.Material()

        material.add(mass)
        self.lammps_wrapper.add(material)

        # create a simulation box
        box = simlammps_ontology.SimulationBox()
        face_x = simlammps_ontology.FaceX(vector=(10, 0, 0))
        face_x.add(simlammps_ontology.Periodic())
        face_y = simlammps_ontology.FaceY(vector=(0, 10, 0))
        face_y.add(simlammps_ontology.Periodic())
        face_z = simlammps_ontology.FaceZ(vector=(0, 0, 10))
        face_z.add(simlammps_ontology.Periodic())
        box.add(face_x, face_y, face_z)
        self.lammps_wrapper.add(box)

        # create a molecular dynamics model
        md_nve = simlammps_ontology.MolecularDynamics()
        self.lammps_wrapper.add(md_nve)

        # create a new solver component:
        sp = simlammps_ontology.SolverParameter()

        # integration time:
        steps = 100
        itime = simlammps_ontology.IntegrationTime(steps=steps)

        sp.add(itime)
        verlet = simlammps_ontology.Verlet()

        sp.add(verlet)
        self.lammps_wrapper.add(sp)

        # define the interatomic force as material relation
        lj = simlammps_ontology.LennardJones612(
            cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
        )
        lj.add(material)
        self.lammps_wrapper.add(lj)

        # Adding one particle
        particle = simlammps_ontology.Atom()
        position = simlammps_ontology.Position(vector=(1, 1, 1))
        velocity = simlammps_ontology.Velocity(vector=(1, 0, 1))
        particle.add(material, position, velocity)
        self.lammps_wrapper.add(particle)

    def test_simple_run(self):
        """
        Tests a simple run
        """
        self.lammps_wrapper.session.run()

    def test_without_velocity(self):
        """
        Tests a simple run where the atom has no velocity
        """
        atom = self.lammps_wrapper.get(oclass=simlammps_ontology.Atom)[0]
        atom.remove(oclass=simlammps_ontology.Velocity)
        self.lammps_wrapper.session.run()


if __name__ == "__main__":
    unittest.main()
