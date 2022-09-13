"""Generic example showing the usage of the wrapper."""

import itertools

from simphony_osp.namespaces import simlammps
from simphony_osp.wrappers import SimLAMMPS

from simphony_osp_simlammps.utils import LAMMPSInputScript


def setup_atoms(parsed_file, material, position_offset):
    """Get atoms from a file and add them with an offset to the container."""
    for pos, vel in parsed_file.atom_information_generator():
        atom = simlammps.Atom()
        position = simlammps.Position(
            vector=(
                pos[0] + position_offset[0],
                pos[1] + position_offset[1],
                pos[2] + position_offset[2],
            )
        )
        vel = simlammps.Velocity(vector=vel)
        atom[simlammps.hasPart] += {material, position, vel}


def setup_box(parsed_file):
    """Creates the box with the coordinates from a file."""
    vector_x, vector_y, vector_z = parsed_file.box_coordinates()
    box = simlammps.SimulationBox()
    face_x = simlammps.FaceX(vector=vector_x)
    face_x[simlammps.hasPart] += simlammps.Periodic()
    face_y = simlammps.FaceY(vector=vector_y)
    face_y[simlammps.hasPart] += simlammps.Periodic()
    face_z = simlammps.FaceZ(vector=vector_z)
    face_z[simlammps.hasPart] += simlammps.Periodic()
    box[simlammps.hasPart] += {face_x, face_y, face_z}


session = SimLAMMPS()
session.locked = True

with session:
    materials = []
    offsets = []
    # Create the materials and masses
    for idx, offset in enumerate(itertools.product([30, 2], repeat=3)):
        mass = simlammps.Mass(value=0.2)
        mat = simlammps.Material()
        mat[simlammps.hasPart] += mass
        materials.append(mat)
        offsets.append(offset)

    # Read input file
    input_file = LAMMPSInputScript("examples/data_input_from_sim.lammps")
    input_file.parse()

    # Add first atoms
    # setup_atoms(input_file, materials[0], offsets[0])
    setup_box(input_file)

    md_nve = simlammps.MolecularDynamics()

    sp = simlammps.SolverParameter()

    # Integration time:
    steps = 500
    itime = simlammps.IntegrationTime(steps=steps)

    sp[simlammps.hasPart] += itime
    verlet = simlammps.Verlet()

    sp[simlammps.hasPart] += verlet

    lj = simlammps.LennardJones612(
        cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
    )
    lj[simlammps.hasPart] += materials[0]

    video = simlammps.Video(steps=25, width=640, height=480)
session.compute()

with session:
    # First material has been added already
    for mat, offset in zip(materials[1:], offsets[1:]):
        setup_atoms(input_file, mat, offset)
session.compute()

with session:
    for atom in session.iter(oclass=simlammps.Atom):
        velocity = atom.get(oclass=simlammps.Velocity).one()
        mat = atom.get(oclass=simlammps.Material).one()
        offset = offsets[materials.index(mat)]
        vel_idx = [1 if a == 2 else -1 for a in offset]
        velocity.vector = tuple(5 * idx for idx in vel_idx)

    # Change the number of steps
    sp = session.get(oclass=simlammps.SolverParameter).one()
    sp.get(oclass=simlammps.IntegrationTime).one().steps = 1000
session.compute()

with session:
    # Update the box dimensions
    box_in_wrapper = session.get(oclass=simlammps.SimulationBox).one()
    box_in_wrapper.get(oclass=simlammps.FaceX).one().vector = (50, 0, 0)
    box_in_wrapper.get(oclass=simlammps.FaceY).one().vector = (0, 50, 0)
    box_in_wrapper.get(oclass=simlammps.FaceZ).one().vector = (0, 0, 50)

session.compute()
