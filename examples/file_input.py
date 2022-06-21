from osp.core.namespaces import simlammps_ontology

from osp.wrappers.simlammps import SimlammpsSession
from osp.wrappers.simlammps.utils import LammpsInputScript

lammps_wrapper = simlammps_ontology.SimlammpsWrapper(session=SimlammpsSession())

mass = simlammps_ontology.Mass(value=0.2)
material = simlammps_ontology.Material()

material.add(mass)
lammps_wrapper.add(material)


input_file = LammpsInputScript("examples/data_input_from_sim.lammps")
input_file.parse()

for coordinates, velocity in input_file.atom_information_generator():
    particle = simlammps_ontology.Atom()
    position = simlammps_ontology.Position(vector=coordinates)
    velocity = simlammps_ontology.Velocity(vector=velocity)
    particle.add(material, position, velocity)
    lammps_wrapper.add(particle)

vector_x, vector_y, vector_z = input_file.box_coordinates()
box = simlammps_ontology.SimulationBox(name="simulation_box")
face_x = simlammps_ontology.FaceX(vector=vector_x)
face_x.add(simlammps_ontology.Periodic())
face_y = simlammps_ontology.FaceY(vector=vector_y)
face_y.add(simlammps_ontology.Periodic())
face_z = simlammps_ontology.FaceZ(vector=vector_z)
face_z.add(simlammps_ontology.Periodic())
box.add(face_x, face_y, face_z)
lammps_wrapper.add(box)

md_nve = simlammps_ontology.MolecularDynamics()
lammps_wrapper.add(md_nve)

sp = simlammps_ontology.SolverParameter()

# integration time:
steps = 1000
itime = simlammps_ontology.IntegrationTime(steps=steps)

sp.add(itime)
verlet = simlammps_ontology.Verlet()

sp.add(verlet)
lammps_wrapper.add(sp)

lj = simlammps_ontology.LennardJones612(
    cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
)

lj.add(material)
lammps_wrapper.add(lj)

# lammps_wrapper.add(simlammps_ontology.Video(steps=10, name="file_input.mp4"))
lammps_wrapper.session.run()

# Update the box dimensions
proxy_box = lammps_wrapper.get(oclass=simlammps_ontology.SimulationBox)[0]
proxy_box.get(oclass=simlammps_ontology.FaceX)[0].vector = (15, 0, 0)
proxy_box.get(oclass=simlammps_ontology.FaceY)[0].vector = (0, 15, 0)
proxy_box.get(oclass=simlammps_ontology.FaceZ)[0].vector = (0, 0, 15)

# Change the number of steps
solver_parameter = lammps_wrapper.get(oclass=simlammps_ontology.SolverParameter)[0]
solver_parameter.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 275

lammps_wrapper.session.run()
