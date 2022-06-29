"""Example showing how to couple and link simulations with the wrapper."""

from simphony_osp.namespaces import simlammps
from simphony_osp.session import Session
from simphony_osp.wrappers import SimLammps

# create the wrappers
session_a = SimLammps()

session_b = SimLammps()

with Session() as workspace:

    # define a material:
    mass = simlammps.Mass(value=0.2)

    material_a = simlammps.Material()
    material_b = simlammps.Material()

    material_a[simlammps.hasPart] += mass
    material_b[simlammps.hasPart] += mass

    # create a simulation box
    box = simlammps.SimulationBox()
    face_x = simlammps.FaceX(vector=(7, 0, 0))
    face_x[simlammps.hasPart] += simlammps.Periodic()
    face_y = simlammps.FaceY(vector=(0, 7, 0))
    face_y[simlammps.hasPart] += simlammps.Periodic()
    face_z = simlammps.FaceZ(vector=(0, 0, 7))
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
    lj[simlammps.hasPart] += {material_a, material_b}

    session_a.add(set(workspace))
    session_b.add(set(workspace))

    material_a = session_a.from_identifier(material_a.identifier)
    material_b = session_b.from_identifier(material_b.identifier)

atom_a = simlammps.Atom(session=session_a)
position_a = simlammps.Position(vector=[3, 2, 3], session=session_a)
atom_a[simlammps.hasPart] += {material_a, position_a}

atom_b = simlammps.Atom(session=session_b)
position_b = simlammps.Position(vector=[3, 5, 3], session=session_b)
atom_b[simlammps.hasPart] += {material_b, position_b}

video_a = simlammps.Video(steps=2, height=640, width=480, session=session_a)
video_b = simlammps.Video(steps=2, height=640, width=480, session=session_b)

session_a.compute()
session_b.compute()

velocity_a = atom_a.get(oclass=simlammps.Velocity).any() or simlammps.Velocity(
    vector=(0, 0, 0), session=session_a
)
velocity_a.vector = (0, 5, 0)
atom_a[simlammps.hasPart] += velocity_a

velocity_b = atom_b.get(oclass=simlammps.Velocity).any() or simlammps.Velocity(
    vector=(0, 0, 0), session=session_b
)
velocity_b.vector = (0, -5, 0)
atom_b[simlammps.hasPart] += velocity_b

sp_a = session_a.get(oclass=simlammps.SolverParameter).one()
sp_a.get(oclass=simlammps.IntegrationTime).one().steps = 1

sp_b = session_b.get(oclass=simlammps.SolverParameter).one()
sp_b.get(oclass=simlammps.IntegrationTime).one().steps = 1


while abs(position_a.vector[1] - position_b.vector[1]) > 0.7:
    session_a.compute()
    session_b.compute()


velocity_a.vector, velocity_b.vector = velocity_b.vector, velocity_a.vector

sp_a.get(oclass=simlammps.IntegrationTime).one().steps = 100
sp_b.get(oclass=simlammps.IntegrationTime).one().steps = 100

session_a.compute()
session_b.compute()

# video_a.operations.download('video_a.mp4')
# video_b.operations.download('video_b.mp4')
