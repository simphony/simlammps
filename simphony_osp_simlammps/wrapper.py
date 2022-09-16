"""LAMMPS wrapper implementation."""

from pathlib import Path
from tempfile import TemporaryDirectory
from typing import BinaryIO, Dict, List, Optional, Tuple

import numpy as np
from lammps import Atom, PyLammps
from simphony_osp.development import Wrapper, get_hash
from simphony_osp.namespaces import owl, simlammps
from simphony_osp.ontology import OntologyIndividual
from simphony_osp.session import Session

from simphony_osp_simlammps.mapper import Mapper


class SimLAMMPS(Wrapper):
    """LAMMPS wrapper implementation."""

    _engine: Optional[PyLammps] = None
    _atom_mapper: Optional[Mapper] = None
    _material_mapper: Optional[Mapper] = None
    _videos: Dict[str, TemporaryDirectory]

    # Interface
    # ↓ ----- ↓

    entity_tracking: bool = True
    """Gives access to lists of added, updated and deleted entities."""

    def open(self, configuration: str, create: bool = False) -> None:
        """Prepare the wrapper for a new simulation.

        Args:
            configuration: Ignored.
            create: Ignored.
        """
        if any(
            x is not None
            for x in (self._engine, self._atom_mapper, self._material_mapper)
        ):
            raise RuntimeError(
                "This wrapper session is already in use, please close it "
                "first."
            )

        self._videos = dict()
        self._engine = PyLammps()
        self._atom_mapper = Mapper()
        self._material_mapper = Mapper()
        self._add_settings()

    def close(self) -> None:
        """Destroy the existing LAMMPS engine instance."""
        self._engine = None
        self._atom_mapper = None
        self._material_mapper = None
        if hasattr(self, "_videos"):
            for video in self._videos.values():
                video.cleanup()
        self._videos = dict()

    def populate(self) -> None:
        """Not required, as there is no pre-existing data to load."""

    def commit(self) -> None:
        """Update data structures on the engine to match the user's desires."""
        # Perform a consistency check if the user changed something. Raises
        # an `AssertionError` if the consistency check fails. This prevents
        # to some extent the case in which the changes are only partially
        # committed.
        if self.added | self.updated | self.deleted:
            self._consistency_check()

        # Ensure that every material in the session is mapped to a LAMMPS
        # material.
        for individual in self.session.get(oclass=simlammps.Material):
            self._map_material(individual)

        def key(
            ontology_individual: OntologyIndividual,
            order: Tuple,
        ) -> int:
            """Process ontology individuals in a certain order.

            Serves as a key for ordering a list of ontology individuals to
            be processed according to the given ordering. If the class of
            the ontology individual is not specified in the ordering,
            then it is processed before the individuals whose classes are
            specified in the ordering.

            Args:
                ontology_individual: The ontology individual to provide a
                    sorting key for.
                order: The preferred ordering of ontology classes.
            """
            index = 0
            for class_ in ontology_individual.superclasses:
                index = max(
                    index,
                    order.index(class_) + 1 if class_ in order else 0,
                )
            return index

        ordering = (
            simlammps.Atom,
            simlammps.Position,
            simlammps.Velocity,
            simlammps.Force,
        )
        for individual in sorted(self.deleted, key=lambda x: key(x, ordering)):
            self._remove_by_type(individual)

        ordering = (
            simlammps.SimulationBox,
            simlammps.Face,
            simlammps.BoundaryCondition,
            simlammps.Material,
            simlammps.Mass,
            simlammps.LennardJones612,
            simlammps.Atom,
            simlammps.Position,
            simlammps.Velocity,
            simlammps.Force,
        )
        for individual in sorted(self.added, key=lambda x: key(x, ordering)):
            self._add_by_type(individual)

        # ordering = (...) does not change
        for individual in sorted(self.updated, key=lambda x: key(x, ordering)):
            self._update_by_type(individual)

    def compute(self) -> None:
        """Run the LAMMPS simulation."""
        # Run the simulation
        sol_param = self.session.get(oclass=simlammps.SolverParameter).one()
        steps = sol_param.get(oclass=simlammps.IntegrationTime).one().steps
        self._engine.run(steps)
        # self._engine.write_dump("all", "atom", "atom_dump.txt")

        # Update the existing entities with the changes
        self._add_delete_atoms_from_backend(self.session)
        for individual in self.session.get(oclass=simlammps.Atom):
            self._update_atom_from_backend(individual)
        for individual in self.session.get(oclass=simlammps.Position):
            self._update_position_from_backend(individual)
        for individual in self.session.get(oclass=simlammps.Velocity):
            self._update_velocity_from_backend(individual)
        for individual in self.session.get(oclass=simlammps.Force):
            self._update_force_from_backend(individual)

    def load(self, key: str) -> BinaryIO:
        """Given the IRI of a video file object, yield its contents."""
        return open(Path(self._videos[str(key)].name) / "video.mp4", "rb")

    def rename(self, key: str, new_key: str) -> None:
        """Change the IRI reference to a video file."""
        if str(key) in self._videos:
            self._videos[str(new_key)] = self._videos[str(key)]
            del self._videos[str(key)]

    def hash(self, key: str) -> str:
        """Get the hash of a video file."""
        return get_hash(str(Path(self._videos[str(key)].name) / "video.mp4"))

    def delete(self, key: str) -> None:
        """Delete a video file.

        This function is just a placeholder, as the video file should not be
        deleted (LAMMPS will continue writing to it). It will be deleted
        when the session is closed.
        """
        pass

    # Interface
    # ↑ ----- ↑

    def _add_delete_atoms_from_backend(self, session: Session):
        """Update atoms in the wrapper with the information from the engine.

        It checks if atoms were created or deleted after a simulation,
        and updates the session.

        Args:
            session: the session where atoms need to be added or removed.
        """
        # TODO: Check if the number of atoms changed
        #   If a new atom was created, create its position

    def _update_atom_from_backend(self, atom: OntologyIndividual):
        """Updates the given atom with new velocities and/or forces.

        Args:
            atom: atom to be updated.
        """
        velocity = atom.get(oclass=simlammps.Velocity)
        # The atom has no velocity
        if not velocity:
            self._update_velocity_from_backend(None, atom)
        force = atom.get(oclass=simlammps.Force)
        # The atom has no force
        if not force:
            self._update_force_from_backend(None, atom)

    def _update_position_from_backend(
        self,
        position: OntologyIndividual,
        ontology_atom: Optional[OntologyIndividual] = None,
    ):
        """Updates a given position object with the latest values in the engine.

        Args:
            position: position object to update.
            ontology_atom: atom that has said position.
        """
        if ontology_atom is None:
            ontology_atom = self._parent_atom(position)
        lammps_atom = self._lammps_atom(ontology_atom)
        position.vector = tuple(lammps_atom.position)

    def _update_velocity_from_backend(
        self,
        velocity: Optional[OntologyIndividual],
        ontology_atom: Optional[OntologyIndividual] = None,
    ):
        """Update a given velocity object with the latest values in the engine.

        If the previous `velocity` was `None`, an ontology_atom MUST be given
        (in case it has to be initialised). If there was a pre-existing value,
        the atom is not required and could be computed.

        Args:
            velocity: velocity object to update.
            ontology_atom: atom that has said velocity.
        """
        if ontology_atom is None:
            ontology_atom = self._parent_atom(velocity)
        lammps_atom = self._lammps_atom(ontology_atom)
        if velocity is not None:
            velocity.vector = tuple(lammps_atom.velocity)
        # There was no velocity and now there is
        elif not np.array_equal(lammps_atom.velocity, (0, 0, 0)):
            if ontology_atom is None:
                message = "Atom is required if there was no previous velocity"
                raise ValueError(message)
            velocity = simlammps.Velocity(vector=lammps_atom.velocity)
            ontology_atom.connect(velocity, rel=simlammps.hasPart)

    def _update_force_from_backend(
        self,
        force: Optional[OntologyIndividual],
        ontology_atom: Optional[OntologyIndividual] = None,
    ):
        """Updates a given force object with the latest values in the engine.

        Args:
            force: force object to update.
            ontology_atom: atom that has said force.
        """
        if ontology_atom is None:
            ontology_atom = self._parent_atom(force)
        lammps_atom = self._lammps_atom(ontology_atom)
        if force is not None:
            force.vector = tuple(lammps_atom.force)
        # There was no force and now there is
        elif not np.array_equal(lammps_atom.force, (0, 0, 0)):
            if ontology_atom is None:
                message = "Atom is required if there was no previous force"
                raise ValueError(message)
            force = simlammps.Force(vector=lammps_atom.force)
            ontology_atom.connect(force, rel=simlammps.hasPart)

    def _add_by_type(self, individual: OntologyIndividual):
        """Adds ontology individuals based on their type to the engine.

        Args:
             individual: object to add.
        """
        if individual.is_a(simlammps.Atom):
            self._add_atom(individual)
        elif individual.is_a(simlammps.Velocity):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.added | self.updated:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_velocity(lammps_atom, individual.vector.data)
        elif individual.is_a(simlammps.Force):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.added | self.updated:
                # Lammps internal id = pylammps id + 1
                lammps_atom_id = (
                    self._atom_mapper.get(ontology_atom.identifier) + 1
                )
                self._set_force(lammps_atom_id, individual.vector.data)
        elif individual.is_a(simlammps.Position):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.added | self.updated:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_position(lammps_atom, individual.vector.data)
        elif individual.is_a(simlammps.Material):
            self._add_material(individual)
        elif individual.is_a(simlammps.SimulationBox):
            if any(x.is_a(simlammps.SimulationBox) for x in self.deleted):
                self._update_simulation_box(individual)
            else:
                self._add_simulation_box(individual)
        elif individual.is_a(simlammps.Face):
            parent_box = individual.get(
                oclass=simlammps.SimulationBox
            ).inverse.one()
            self._update_simulation_box(parent_box)
            # As in `_update_by_type`, the simulation box info can be updated
            # several times on the engine, but this is not an issue.
        elif individual.is_a(simlammps.BoundaryCondition):
            parent_box = (
                individual.get(oclass=simlammps.Face)
                .inverse.one()
                .get(oclass=simlammps.SimulationBox)
                .inverse.one()
            )
            self._update_simulation_box(parent_box)
            # As in `_update_by_type`, the simulation box info can be updated
            # several times on the engine, but this is not an issue.
        elif individual.is_a(simlammps.LennardJones612):
            self._add_pair_style(individual)
        elif individual.is_a(simlammps.Thermostat):
            self._define_fix(individual)
        elif individual.is_a(simlammps.Video):
            temp_dir = TemporaryDirectory()
            path = Path(temp_dir.name) / "video.mp4"
            self._videos[str(individual.identifier)] = temp_dir
            video = (
                individual.steps,
                path,
                individual.width,
                individual.height,
            )
            self._output_video(*video)
        else:
            # message = "Adding {} does not add anything to the engine."
            # (message.format(individual))
            pass

    def _update_by_type(self, individual: OntologyIndividual):
        """Updates ontology individuals objects based on their type.

        Args:
            individual: ontology individual to update
        """
        # Nothing if the atom is changed (should be the pos, vel or force)
        if individual.is_a(simlammps.Position):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.updated | self.added:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_position(lammps_atom, individual.vector.data)
        elif individual.is_a(simlammps.Velocity):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.updated | self.added:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_velocity(lammps_atom, individual.vector.data)
        elif individual.is_a(simlammps.Force):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.updated | self.added:
                # Lammps internal id = pylammps id + 1
                lammps_atom_id = (
                    self._atom_mapper.get(ontology_atom.identifier) + 1
                )
                self._set_force(lammps_atom_id, individual.vector.data)
        elif individual.is_a(simlammps.Atom):
            ontology_atom = individual
            lammps_atom = self._lammps_atom(ontology_atom)
            lammps_atom_id = (
                self._atom_mapper.get(ontology_atom.identifier) + 1
            )
            position = ontology_atom.get(oclass=simlammps.Position).any()
            velocity = ontology_atom.get(oclass=simlammps.Velocity).any()
            force = ontology_atom.get(oclass=simlammps.Force).any()
            self._set_position(
                lammps_atom,
                position.vector.data if position is not None else [0, 0, 0],
            )
            self._set_velocity(
                lammps_atom,
                velocity.vector.data if velocity is not None else [0, 0, 0],
            )
            self._set_force(
                lammps_atom_id,
                force.vector.data if force is not None else [0, 0, 0],
            )
        elif individual.is_a(simlammps.Face):
            box = individual.get(oclass=simlammps.SimulationBox).inverse.one()
            self._update_simulation_box(box)
            # The above can in fact update the simulation box several times
            # if various faces (and other combinations like one face and the
            # box) are updated or added, but updating it several times does
            # not cause a problem.
        elif individual.is_a(simlammps.BoundaryCondition):
            box = (
                individual.get(oclass=simlammps.Face)
                .inverse.one()
                .get(oclass=simlammps.SimulationBox)
                .inverse.one()
            )
            self._update_simulation_box(box)
        elif individual.is_a(simlammps.Material):
            self._add_material(individual)
        elif individual.is_a(simlammps.SimulationBox):
            self._update_simulation_box(individual)
        elif individual.is_a(simlammps.LennardJones612):
            self._engine.units("lj")
            self._add_by_type(individual)
        elif individual.is_a(simlammps.Thermostat):
            self._define_fix(individual)
        elif individual.is_a(simlammps.Video):
            message = (
                "Changing video {} does not affect the engine. If you "
                "want to produce a video with different "
                "characteristics, create a new video object."
            )
            print(message.format(individual))
        else:
            # message = "Updating {} does not affect the engine."
            # print(message.format(individual))
            pass

    def _remove_by_type(
        self,
        individual: OntologyIndividual,
    ):
        """Removes ontology individuals based on their type on the engine.

        Args:
            individual: ontology individual to remove.
        """
        if individual.is_a(simlammps.Atom):
            # Lammps internal id = pylammps id + 1
            lammps_atom_id = self._atom_mapper.get(individual.identifier) + 1
            self._remove_atom(lammps_atom_id)
        elif individual.is_a(simlammps.Position):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.deleted:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_position(lammps_atom, [0, 0, 0])
        elif individual.is_a(simlammps.Velocity):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.deleted:
                lammps_atom = self._lammps_atom(ontology_atom)
                self._set_velocity(lammps_atom, [0, 0, 0])
        elif individual.is_a(simlammps.Force):
            ontology_atom = self._parent_atom(individual)
            if ontology_atom not in self.deleted:
                # Lammps internal id = pylammps id + 1
                lammps_atom_id = (
                    self._atom_mapper.get(ontology_atom.identifier) + 1
                )
                self._set_force(lammps_atom_id, [0, 0, 0])
        elif individual.is_a(simlammps.BoundaryCondition):
            parent_box = (
                individual.get(oclass=simlammps.Face)
                .inverse.one()
                .get(oclass=simlammps.SimulationBox)
                .inverse.one()
            )
            if parent_box not in self.deleted:
                self._update_simulation_box(parent_box)
            # As in `_update_by_type`, the simulation box info can be updated
            # several times on the engine, but this is not an issue.
        else:
            # message = "Removing {} does not affect the engine."
            # print(message.format(individual))
            pass

    def _output_video(self, steps: int, name: str, width: int, height: int):
        """Saves the execution of LAMMPS to a video.

        Args:
            steps: frequency for the video
            name: name for the file (with extension)
            width: width of the video (in pixels)
            height: height of the video (in pixels)
        """
        self._engine.dump(
            "video_dump",
            "all",
            "movie",
            steps,
            name,
            "type",
            "type",
            "size",
            width,
            height,
        )

    def _add_atom(self, atom: OntologyIndividual):
        """Adds one atom to the engine.

        Args:
            atom: Atom to add.
        """
        material_id = atom.get(oclass=simlammps.Material).one().identifier
        # Atom types start at 1
        atom_type = self._material_mapper.get(material_id) + 1
        position_vector = atom.get(oclass=simlammps.Position).one().vector.data

        # Position vector has x, y and z components
        self._engine.create_atoms(atom_type, "single", *position_vector)
        # Add the atom to the mapper
        lammps_atom_id = self._atom_mapper.add(atom.identifier)
        lammps_atom = self._engine.atoms[lammps_atom_id]

        velocity = atom.get(oclass=simlammps.Velocity)
        if velocity:
            velocity = velocity.one()
            self._set_velocity(lammps_atom, velocity.vector.data)

        force = atom.get(oclass=simlammps.Force)
        if force:
            force = force.one()
            # LAMMPS internal id = pylammps id + 1
            self._set_force(lammps_atom_id + 1, force.vector.data)

    def _add_settings(self, atom_style: str = "atomic"):
        """Defines the general engine settings.

        Args:
            atom_style: atom style.
        """
        self._engine.atom_style(atom_style)
        self._engine.atom_modify("map", "array")
        self._engine.neighbor(0.3, "bin")
        self._engine.neigh_modify("delay", 5)

    def _add_simulation_box(self, simulation_box: OntologyIndividual):
        """Adds the simulation box to the engine.

        Args:
            simulation_box: instance of a simulation box.
        """
        if self.session.get(oclass=simlammps.LennardJones612):
            self._engine.units("lj")

        face_x = simulation_box.get(oclass=simlammps.FaceX).one()
        face_y = simulation_box.get(oclass=simlammps.FaceY).one()
        face_z = simulation_box.get(oclass=simlammps.FaceZ).one()
        style_x = self._find_boundary_condition_style(face_x)
        style_y = self._find_boundary_condition_style(face_y)
        style_z = self._find_boundary_condition_style(face_z)

        name = simulation_box.label or "Simulation_Box"
        origin = [0, 0, 0]

        self._engine.dimension(3)
        self._engine.boundary(style_x, style_y, style_z)
        self._engine.region(
            name,
            "block",
            origin[0],
            origin[0] + face_x.vector[0],
            origin[1],
            origin[1] + face_y.vector[1],
            origin[2],
            origin[2] + face_z.vector[2],
        )
        self._engine.create_box(len(self._material_mapper), name)

        self._define_fix(None)

    def _add_pair_style(self, lj: OntologyIndividual):
        """Defines the settings for the pair style.

        Args:
            lj: lennard-jones individual.
        """
        if lj:
            self._engine.pair_style("lj/cut", float(lj.cutoffDistance))
            self._engine.pair_coeff(
                "*",
                "*",
                float(lj.energyWellDepth),
                float(lj.vanDerWaalsRadius),
            )

    def _define_fix(self, thermo: Optional[OntologyIndividual] = None):
        """Defines the fixes.

        Fixes are operations applied to the system during timestepping
        or minimization

        Args:
            thermo: thermostat.
        """
        if thermo is None:
            self._engine.fix(1, "all", "nve")
        else:
            message = "No thermostat supported yet"
            print(message)

    def _add_material(self, material: OntologyIndividual):
        """Adds a material to the engine.

        Args:
            material: instance of a material
        """
        mass = material.get(oclass=simlammps.Mass).one()
        try:
            # Atom types start at 1
            atom_type = self._material_mapper.get(material.identifier) + 1
        except KeyError:
            self._material_mapper.add(material.identifier)
            atom_type = len(self._material_mapper)
        self._engine.mass(atom_type, float(mass.value))

    @staticmethod
    def _set_position(lammps_atom: Atom, position_vector: List[float]):
        """Updates the position of an atom from LAMMPS.

        Args:
            lammps_atom: atom in LAMMPS.
            position_vector: new position values.
        """
        lammps_atom.position = position_vector

    @staticmethod
    def _set_velocity(lammps_atom: Atom, velocity_vector: List[float]):
        """Updates the velocity of an atom from LAMMPS.

        Args:
            lammps_atom: atom in LAMMPS.
            velocity_vector: new velocity values.
        """
        lammps_atom.velocity = velocity_vector

    def _set_force(self, lammps_atom_id: int, force_vector: List[float]):
        """Sets the force to the atom.

        Args:
            lammps_atom_id: id of the atom in lammps.
            force_vector: vector with the force values.
        """
        # FIXME: Individual forces set to atoms should be made persistent
        # Add the atom to a temporal group
        self._engine.group("temp", "id", "==", lammps_atom_id)
        self._engine.fix(
            "fAtom" + str(lammps_atom_id), "temp", "setforce", *force_vector
        )
        # Delete the group
        # self._engine.group("temp", "delete")

    def _update_simulation_box(self, simulation_box: OntologyIndividual):
        """Updates the simulation box.

        Args:
            simulation_box: instance of a simulation box.
        """
        origin = [0, 0, 0]

        face_x = simulation_box.get(oclass=simlammps.FaceX).one()
        face_y = simulation_box.get(oclass=simlammps.FaceY).one()
        face_z = simulation_box.get(oclass=simlammps.FaceZ).one()

        style_x = self._find_boundary_condition_style(face_x)
        style_y = self._find_boundary_condition_style(face_y)
        style_z = self._find_boundary_condition_style(face_z)

        self._engine.change_box(
            "all",
            "x",
            "final",
            origin[0],
            origin[0] + face_x.vector[0],
            "y",
            "final",
            origin[1],
            origin[1] + face_y.vector[1],
            "z",
            "final",
            origin[2],
            origin[2] + face_z.vector[2],
            "boundary",
            style_x,
            style_y,
            style_z,
        )

    def _remove_atom(self, lammps_atom_id: int):
        """Removes an atom from LAMMPS.

        Args:
            lammps_atom_id: id in LAMMPS of the atom to remove.
        """
        # Add the atom to a temporal group
        self._engine.group("temp", "id", "==", lammps_atom_id)
        # Remove the atoms from the group without re-assigning IDs
        self._engine.delete_atoms("group", "temp", "compress", "no")
        # Delete the group
        self._engine.group("temp", "delete")
        # Update the mapper
        self._atom_mapper.remove(lammps_atom_id)

    def _map_material(self, material: OntologyIndividual):
        """Maps the uid of a material to a lammps atom type.

        Args:
            material: instance of the material.
        """
        identifier = material.identifier
        if identifier not in self._material_mapper:
            self._material_mapper.add(identifier)

    @staticmethod
    def _find_boundary_condition_style(face: OntologyIndividual) -> str:
        """Processes face to find the style of the boundary condition.

        Can be periodic or fixed.

        Args:
            face: face of the boundary.

        Returns
            'p' for periodic or 'f' for fixed.
        """
        # Condition can be periodic or fixed
        periodic = face.get(oclass=simlammps.Periodic)

        # Checker already makes sure there is one and only one
        if periodic is not None:
            return "p"
        return "f"

    @staticmethod
    def _parent_atom(
        individual: OntologyIndividual,
    ) -> Optional[OntologyIndividual]:
        """Gets the atom corresponding to a given ontology individual object.

        Mainly used to know the atom given a position, velocity.

        Args:
            individual: object related to an atom.

        Returns:
            The atom, or `None` if the individual has no parent atom.
        """
        ontology_atom = individual.get(
            rel=owl.topObjectProperty, oclass=simlammps.Atom
        ).inverse.any()
        return ontology_atom

    def _lammps_atom(self, ontology_atom: OntologyIndividual) -> Atom:
        """Gets the lammps atom corresponding to a given ontology atom.

        Args:
            ontology_atom: instance of an atom.

        Returns:
            lammps_atom: the atom in lammps
        """
        lammps_atom_id = self._atom_mapper.get(ontology_atom.identifier)
        return self._engine.atoms[lammps_atom_id]

    def _consistency_check(self) -> None:
        """Consistency check.

        Before updating the data structures, check that the changes
        provided by the user can leave them in a consistent state.

        This necessary because SimPhoNy cannot revert the changes you
        make to your LAMMPS data structures.

        Raises:
            AssertionError: When the data provided by the user would leave
                LAMMPS in an inconsistent or unpredictable state.
        """
        try:
            # Verify simulation box
            simulation_box = self.session.get(
                oclass=simlammps.SimulationBox
            ).one()
            face_x = simulation_box.get(oclass=simlammps.FaceX).one()
            face_y = simulation_box.get(oclass=simlammps.FaceY).one()
            face_z = simulation_box.get(oclass=simlammps.FaceZ).one()
            assert len(self.session.get(oclass=simlammps.Face)) == 3
            array_x = face_x.vector.data
            assert array_x.dtype in ("int64", "float64")
            assert array_x.shape == (3,)
            array_y = face_y.vector.data
            assert array_y.dtype in ("int64", "float64")
            assert array_y.shape == (3,)
            array_z = face_z.vector.data
            assert array_z.dtype in ("int64", "float64")
            assert array_z.shape == (3,)
            assert len(simulation_box.get(oclass=simlammps.FaceX)) == 1
            assert len(simulation_box.get(oclass=simlammps.FaceY)) == 1
            assert len(simulation_box.get(oclass=simlammps.FaceZ)) == 1

            # Verify LennardJones potential
            lj = self.session.get(oclass=simlammps.LennardJones612).one()
            assert float(lj.cutoffDistance) is not None
            assert float(lj.energyWellDepth) is not None
            assert float(lj.vanDerWaalsRadius) is not None

            # Verify materials
            for material in self.session.get(oclass=simlammps.Material):
                assert len(material.get(oclass=simlammps.Mass)) == 1

            # Verify atoms
            # - all atoms have at most one velocity, position and force. If
            #   they are present, they have valid values.
            for atom in self.session.get(oclass=simlammps.Atom):
                assert 0 <= len(atom.get(oclass=simlammps.Velocity)) <= 1
                assert 0 <= len(atom.get(oclass=simlammps.Position)) <= 1
                assert 0 <= len(atom.get(oclass=simlammps.Force)) <= 1
                velocity = atom.get(oclass=simlammps.Velocity).any()
                position = atom.get(oclass=simlammps.Position).any()
                force = atom.get(oclass=simlammps.Force).any()
                for entity in filter(None, (velocity, position, force)):
                    array = entity.vector.data
                    assert array.dtype in ("int64", "float64")
                    assert array.shape == (3,)

            # Verify positions, forces and velocities
            # - all positions, forces and velocities are attached to exactly
            # one atom.
            for entity in (
                set(self.session.get(oclass=simlammps.Velocity))
                | set(self.session.get(oclass=simlammps.Position))
                | set(self.session.get(oclass=simlammps.Force))
            ):
                assert (
                    len(
                        entity.get(
                            rel=owl.topObjectProperty, oclass=simlammps.Atom
                        ).inverse
                    )
                    == 1
                )

        except Exception as e:
            raise AssertionError(
                "Your changes leave LAMMPS in an inconsistent or "
                "unpredictable state, cannot commit. Scroll up to find out "
                "the detailed cause of the exception."
            ) from e
