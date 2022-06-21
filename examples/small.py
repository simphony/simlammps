from random import randint

from osp.core.namespaces import simlammps_ontology

from osp.wrappers.simlammps import SimlammpsSession

# create the wrapper
sess = SimlammpsSession()
lammps_wrapper = simlammps_ontology.SimlammpsWrapper(session=sess)

# define a material:
mass = simlammps_ontology.Mass(value=0.2)

material = simlammps_ontology.Material()

material.add(mass)
lammps_wrapper.add(material)

# create the particles

for i in range(3):
    particle = simlammps_ontology.Atom()
    # Careful. Issues if 2 atoms on the same place
    x = randint(1, 6)
    y = randint(1, 6)
    z = randint(1, 6)
    position = simlammps_ontology.Position(vector=(x, y, z))
    velocity = simlammps_ontology.Velocity(vector=(1, 0, 0))
    particle.add(material, position, velocity)
    lammps_wrapper.add(particle)

# create a simulation box
box = simlammps_ontology.SimulationBox()
face_x = simlammps_ontology.FaceX(vector=(10, 0, 0))
face_x.add(simlammps_ontology.Periodic())
face_y = simlammps_ontology.FaceY(vector=(0, 10, 0))
face_y.add(simlammps_ontology.Periodic())
face_z = simlammps_ontology.FaceZ(vector=(0, 0, 10))
face_z.add(simlammps_ontology.Periodic())
box.add(face_x, face_y, face_z)
lammps_wrapper.add(box)


# create a molecular dynamics model
md_nve = simlammps_ontology.MolecularDynamics()
lammps_wrapper.add(md_nve)

# create a new solver component:
sp = simlammps_ontology.SolverParameter()

# integration time:
steps = 100
itime = simlammps_ontology.IntegrationTime(steps=steps)

sp.add(itime)
verlet = simlammps_ontology.Verlet()

sp.add(verlet)
lammps_wrapper.add(sp)


# define the interatomic force as material relation
lj = simlammps_ontology.LennardJones612(
    cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
)
lj.add(material)
lammps_wrapper.add(lj)


particle = simlammps_ontology.Atom()
# Careful. Issues if 2 atoms on the same place
x = randint(1, 6)
y = randint(1, 6)
z = randint(1, 6)
position = simlammps_ontology.Position(vector=(x, y, z))
velocity = simlammps_ontology.Velocity(vector=(1, 0, 1))
particle.add(material, position, velocity)
# Adding one particle
lammps_wrapper.add(particle)
lammps_particle = lammps_wrapper.get(particle.uid)
lammps_position = lammps_particle.get(oclass=simlammps_ontology.Position)[0]
print(str(particle.uid) + ":")
print(" - Initial position: " + str(lammps_position.vector))


# lammps_wrapper.add(simlammps_ontology.Video(steps=10, name="small_test.mp4"))
lammps_wrapper.session.run()

print(" - Position after run: " + str(lammps_position.vector))
print("Changing position manually")
# position.vector = (7, 7, 7)
# lammps_particle.update(position)
# Equal to:
lammps_position.vector = (7, 7, 7)
print(" - New position: " + str(lammps_position.vector))
lammps_wrapper.session.run()
print(" - Position after run: " + str(lammps_position.vector))
