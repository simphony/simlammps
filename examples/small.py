"""Set-up and run a small simulation."""

from random import randint

from simphony_osp.namespaces import simlammps
from simphony_osp.wrappers import SimLAMMPS

# create the wrapper
session = SimLAMMPS()
session.lock = True

with session:
    # define a material:
    mass = simlammps.Mass(value=0.2)

    material = simlammps.Material()

    material[simlammps.hasPart] += mass

    # create the particles

    for i in range(3):
        particle = simlammps.Atom()
        # Careful. Issues if 2 atoms on the same place
        x = randint(1, 6)
        y = randint(1, 6)
        z = randint(1, 6)
        position = simlammps.Position(vector=(x, y, z))
        velocity = simlammps.Velocity(vector=(1, 0, 0))
        particle[simlammps.hasPart] += {material, position, velocity}

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
    md_nve = simlammps.MolecularDynamics()

    # create a new solver component:
    sp = simlammps.SolverParameter()

    # integration time:
    steps = 100
    itime = simlammps.IntegrationTime(steps=steps)

    sp[simlammps.hasPart] += itime
    verlet = simlammps.Verlet()

    sp[simlammps.hasPart] += verlet

    # define the interatomic force as material relation
    lj = simlammps.LennardJones612(
        cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
    )
    lj[simlammps.hasPart] += material

    particle = simlammps.Atom()
    # Careful. Issues if 2 atoms on the same place
    x = randint(1, 6)
    y = randint(1, 6)
    z = randint(1, 6)
    position = simlammps.Position(vector=(x, y, z))
    velocity = simlammps.Velocity(vector=(1, 0, 1))
    particle[simlammps.hasPart] += {material, position, velocity}
    # Adding one particle
    lammps_particle = session.get(particle.identifier)
    lammps_position = lammps_particle.get(oclass=simlammps.Position).one()
    print(str(particle.identifier) + ":")
    print(" - Initial position: " + str(lammps_position.vector))

    video = simlammps.Video(
        steps=10,
        width=640,
        height=480,
    )

    session.compute()

    print(" - Position after run: " + str(lammps_position.vector))
    print("Changing position manually")
    lammps_position.vector = (7, 7, 7)
    print(" - New position: " + str(lammps_position.vector))
    session.compute()
    print(" - Position after run: " + str(lammps_position.vector))
