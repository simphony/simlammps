from osp.core.namespaces import simlammps_ontology

from osp.wrappers.simlammps import SimlammpsSession

# create the wrappers
sess_a = SimlammpsSession()
wrapper_a = simlammps_ontology.SimlammpsWrapper(session=sess_a)

sess_b = SimlammpsSession()
wrapper_b = simlammps_ontology.SimlammpsWrapper(session=sess_b)

# define a material:
mass = simlammps_ontology.Mass(value=0.2)

material_a = simlammps_ontology.Material()
material_b = simlammps_ontology.Material()

material_a.add(mass)
material_b.add(mass)

# create a simulation box
box = simlammps_ontology.SimulationBox()
face_x = simlammps_ontology.FaceX(vector=(7, 0, 0))
face_x.add(simlammps_ontology.Periodic())
face_y = simlammps_ontology.FaceY(vector=(0, 7, 0))
face_y.add(simlammps_ontology.Periodic())
face_z = simlammps_ontology.FaceZ(vector=(0, 0, 7))
face_z.add(simlammps_ontology.Periodic())
box.add(face_x, face_y, face_z)


# create a molecular dynamics model
md_nve = simlammps_ontology.MolecularDynamics()

# create a new solver component:
sp = simlammps_ontology.SolverParameter()

# integration time:
steps = 100
itime = simlammps_ontology.IntegrationTime(steps=steps)

sp.add(itime)
verlet = simlammps_ontology.Verlet()

sp.add(verlet)


# define the interatomic force as material relation
lj = simlammps_ontology.LennardJones612(
    cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
)
lj.add(material_a)
lj.add(material_b)


wrapper_a.add(material_a, material_b, box, md_nve, sp, lj)
wrapper_b.add(material_a, material_b, box, md_nve, sp, lj)


atom_a = simlammps_ontology.Atom(session=sess_a)

position_a = simlammps_ontology.Position(vector=(3, 2, 3), session=sess_a)
atom_a.add(material_a, position_a)

atom_b = simlammps_ontology.Atom(session=sess_b)
position_b = simlammps_ontology.Position(vector=(3, 5, 3), session=sess_b)
atom_b.add(material_b, position_b)

wrapper_a.add(atom_a)
wrapper_b.add(atom_b)

wrapper_a.add(simlammps_ontology.Video(steps=2, name="coupling_linking_a.mp4"))
wrapper_b.add(simlammps_ontology.Video(steps=2, name="coupling_linking_b.mp4"))

wrapper_a.session.run()
wrapper_b.session.run()

velocity_a = simlammps_ontology.Velocity(vector=(0, 5, 0), session=sess_a)
velocity_b = simlammps_ontology.Velocity(vector=(0, -5, 0), session=sess_b)

atom_a.add(velocity_a)
atom_b.add(velocity_b)


sp_a = wrapper_a.get(oclass=simlammps_ontology.SolverParameter)[0]
sp_a.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 1

sp_b = wrapper_b.get(oclass=simlammps_ontology.SolverParameter)[0]
sp_b.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 1


while abs(position_a.vector[1] - position_b.vector[1]) > 0.7:
    wrapper_a.session.run()
    wrapper_b.session.run()


velocity_a.vector, velocity_b.vector = velocity_b.vector, velocity_a.vector

sp_a.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 100
sp_b.get(oclass=simlammps_ontology.IntegrationTime)[0].steps = 100

wrapper_a.session.run()
wrapper_b.session.run()
