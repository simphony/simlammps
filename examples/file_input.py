"""Example showing how to set up a simulation using a LAMMPS script."""

from simphony_osp.namespaces import simlammps
from simphony_osp.wrappers import SimLAMMPS

from simphony_osp_simlammps.utils import LAMMPSInputScript

lammps_session = SimLAMMPS("examples/data_input_from_sim.lammps")
lammps_session.locked = True

with lammps_session:
    mass = simlammps.Mass(value=0.2)
    material = simlammps.Material()

    material[simlammps.hasPart] += mass

    input_file = LAMMPSInputScript("examples/data_input_from_sim.lammps")
    input_file.parse()

    for coordinates, velocity in input_file.atom_information_generator():
        particle = simlammps.Atom()
        position = simlammps.Position(vector=coordinates)
        velocity = simlammps.Velocity(vector=velocity)
        particle[simlammps.hasPart] += {material, position, velocity}

    vector_x, vector_y, vector_z = input_file.box_coordinates()
    box = simlammps.SimulationBox()
    face_x = simlammps.FaceX(vector=vector_x)
    face_y = simlammps.FaceY(vector=vector_y)
    face_y[simlammps.hasPart] += simlammps.Periodic()
    face_z = simlammps.FaceZ(vector=vector_z)
    face_z[simlammps.hasPart] += simlammps.Periodic()
    box[simlammps.hasPart] += {face_x, face_y, face_z}

    md_nve = simlammps.MolecularDynamics()

    solver_parameters = simlammps.SolverParameter()

    # integration time:
    steps = 1000
    itime = simlammps.IntegrationTime(steps=steps)

    solver_parameters[simlammps.hasPart] += itime
    verlet = simlammps.Verlet()

    solver_parameters[simlammps.hasPart] += verlet

    lj = simlammps.LennardJones612(
        cutoffDistance=2.5, energyWellDepth=1.0, vanDerWaalsRadius=1.0
    )

    lj[simlammps.hasPart] += material

    video = simlammps.Video(steps=10, width=640, height=480)
lammps_session.compute()

# Update the box dimensions
proxy_box = lammps_session.get(oclass=simlammps.SimulationBox).one()
proxy_box.get(oclass=simlammps.FaceX).one().vector = (15, 0, 0)
proxy_box.get(oclass=simlammps.FaceY).one().vector = (0, 15, 0)
proxy_box.get(oclass=simlammps.FaceZ).one().vector = (0, 0, 15)

# Change the number of steps
solver_parameter = lammps_session.get(oclass=simlammps.SolverParameter).one()
solver_parameter.get(oclass=simlammps.IntegrationTime).one().steps = 275

lammps_session.compute()
