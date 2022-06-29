"""Creates a simple run for testing the wrapper."""

import unittest

from simphony_osp.namespaces import simlammps
from simphony_osp.session import Session
from simphony_osp.wrappers import SimLammps


class TestSimple(unittest.TestCase):
    """A test consisting on running a simple simulation."""

    session: Session

    def setUp(self):
        """Configure the simulation inputs for the test."""
        session = SimLammps()
        session.locked = True

        with session:
            # define a material:
            mass = simlammps.Mass(value=0.2)
            material = simlammps.Material()

            material.connect(mass, rel=simlammps.hasPart)

            # create a simulation box
            box = simlammps.SimulationBox()
            face_x = simlammps.FaceX(vector=(10, 0, 0))
            face_x[simlammps.hasPart] += simlammps.Periodic()
            face_y = simlammps.FaceY(vector=(0, 10, 0))
            face_y[simlammps.hasPart] += simlammps.Periodic()
            face_z = simlammps.FaceZ(vector=(0, 0, 10))
            face_z[simlammps.hasPart] += simlammps.Periodic()
            box[simlammps.hasPart] += {face_x, face_y, face_z}

            # create a molecular dynamics model
            simlammps.MolecularDynamics()

            # create a new solver component:
            solver_parameter = simlammps.SolverParameter()

            # integration time:
            steps = 100
            itime = simlammps.IntegrationTime(steps=steps)

            solver_parameter[simlammps.hasPart] += itime
            verlet = simlammps.Verlet()

            solver_parameter[simlammps.hasPart] += verlet

            # define the interatomic force as material relation
            lj = simlammps.LennardJones612(
                cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
            )
            lj[simlammps.hasPart] += material

            # Adding one particle
            particle = simlammps.Atom()
            position = simlammps.Position(vector=(1, 1, 1))
            velocity = simlammps.Velocity(vector=(1, 0, 1))
            particle[simlammps.hasPart] += {material, position, velocity}
        session.commit()

        self.session = session

    def test_simple_run(self):
        """Tests a simple run."""
        self.session.compute()

    def test_without_velocity(self):
        """Tests a simple run where the atom has no velocity."""
        atom = self.session.get(oclass=simlammps.Atom).one()
        self.session.delete(atom.get(oclass=simlammps.Velocity))
        self.session.compute()


if __name__ == "__main__":
    unittest.main()
