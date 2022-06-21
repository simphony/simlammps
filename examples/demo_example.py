import itertools

from osp.core.namespaces import simlammps_ontology

from osp.wrappers.simlammps import SimlammpsSession
from osp.wrappers.simlammps.utils import LammpsInputScript


def setup_atoms(container, parsed_file, material, position_offset):
    """
    Get the atoms from a file and adds them with an offset to the container
    """
    for pos, vel in parsed_file.atom_information_generator():
        atom = simlammps_ontology.Atom()
        position = simlammps_ontology.Position(
            vector=(
                pos[0] + position_offset[0],
                pos[1] + position_offset[1],
                pos[2] + position_offset[2],
            )
        )
        vel = simlammps_ontology.Velocity(vector=vel)
        atom.add(material, position, vel)
        container.add(atom)


def setup_box(container, parsed_file):
    """Creates the box with the coordinates from a file."""
    vector_x, vector_y, vector_z = parsed_file.box_coordinates()
    box = simlammps_ontology.SimulationBox(name="simulation_box")
    face_x = simlammps_ontology.FaceX(vector=vector_x)
    face_x.add(simlammps_ontology.Periodic())
    face_y = simlammps_ontology.FaceY(vector=vector_y)
    face_y.add(simlammps_ontology.Periodic())
    face_z = simlammps_ontology.FaceZ(vector=vector_z)
    face_z.add(simlammps_ontology.Periodic())
    box.add(face_x, face_y, face_z)
    container.add(box)


# Create the wrapper
md_wrapper = simlammps_ontology.SimlammpsWrapper(session=SimlammpsSession())

materials = []
offsets = []
# Create the materials and masses
for idx, offset in enumerate(itertools.product([30, 2], repeat=3)):
    mass = simlammps_ontology.Mass(value=0.2)
    mat = simlammps_ontology.Material()
    mat.add(mass)
    md_wrapper.add(mat)
    materials.append(mat)
    offsets.append(offset)

# Read input file
input_file = LammpsInputScript("examples/data_input_from_sim.lammps")
input_file.parse()

# Add first atoms
# setup_atoms(md_wrapper, input_file, materials[0], offsets[0])
setup_box(md_wrapper, input_file)

md_nve = simlammps_ontology.MolecularDynamics()
md_wrapper.add(md_nve)

sp = simlammps_ontology.SolverParameter()

# Integration time:
steps = 500
itime = simlammps_ontology.IntegrationTime(steps=steps)

sp.add(itime)
verlet = simlammps_ontology.Verlet()

sp.add(verlet)
md_wrapper.add(sp)

lj = simlammps_ontology.LennardJones612(
    cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
)
lj.add(materials[0])
md_wrapper.add(lj)

md_wrapper.add(simlammps_ontology.Video(steps=25, name="demo_example.mp4"))

md_wrapper.session.run()
# First material has been added already
for mat, offset in zip(materials[1:], offsets[1:]):
    setup_atoms(md_wrapper, input_file, mat, offset)
    md_wrapper.session.run()

for atom in md_wrapper.iter(oclass=simlammps_ontology.Atom):
    velocity = atom.get(oclass=simlammps_ontology.Velocity)[0]
    mat = atom.get(oclass=simlammps_ontology.Material)[0]
    offset = offsets[materials.index(mat)]
    vel_idx = [1 if a == 2 else -1 for a in offset]
    velocity.vector = tuple(5 * idx for idx in vel_idx)

# Change the number of steps
sp = md_wrapper.get(oclass=simlammps_ontology.SolverParameter)[0]
sp.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 1000
md_wrapper.session.run()

# Update the box dimensions
box_in_wrapper = md_wrapper.get(oclass=simlammps_ontology.SimulationBox)[0]
box_in_wrapper.get(oclass=simlammps_ontology.FaceX)[0].vector = (50, 0, 0)
box_in_wrapper.get(oclass=simlammps_ontology.FaceY)[0].vector = (0, 50, 0)
box_in_wrapper.get(oclass=simlammps_ontology.FaceZ)[0].vector = (0, 0, 50)

md_wrapper.session.run()
