"""Session class for the LAMMPS engine."""

from lammps import PyLammps
from osp.core.namespaces import cuba, simlammps_ontology
from osp.core.session import SimWrapperSession

from osp.wrappers.simlammps.mapper import Mapper


class SimlammpsSession(SimWrapperSession):
    """
    Session class for the LAMMPS engine.
    """

    def __init__(self, engine=None, **kwargs):
        if engine is None:
            engine = PyLammps()
        super().__init__(engine, **kwargs)
        self._atom_mapper = Mapper()
        self._material_mapper = Mapper()

    def __str__(self):
        return "Simlammps Wrapper Session"

    # OVERRIDE
    def _initialize(self, root_obj, buffer):
        materials = []
        atoms = []
        thermostat = None
        video = None
        for cuds_object in buffer.values():
            oclass = cuds_object.oclass
            if oclass == simlammps_ontology.Material:
                materials.append(cuds_object)
                # Has to be mapped now for the simulation box
                self._map_material(cuds_object)
            elif oclass == simlammps_ontology.SimulationBox:
                simulation_box = cuds_object
            elif oclass == simlammps_ontology.LennardJones612:
                lj = cuds_object
                self._engine.units("lj")
            elif oclass == simlammps_ontology.Thermostat:
                thermostat = cuds_object
            elif oclass == simlammps_ontology.Atom:
                atoms.append(cuds_object)
            elif oclass == simlammps_ontology.Video:
                video = (
                    cuds_object.steps,
                    cuds_object.name,
                    cuds_object.width,
                    cuds_object.height,
                )
            else:
                # TODO: Other types?
                # Bonds?
                pass

        self._add_settings()
        self._add_simulation_box(simulation_box)
        self._add_pair_style(lj)
        self._define_fix(thermostat)
        for mat in materials:
            self._add_material(mat)
        for atom in atoms:
            self._add_atom(atom)
        if video:
            self._output_video(*video)

    # OVERRIDE
    def _run(self, root_cuds_object):
        sol_param = root_cuds_object.get(oclass=simlammps_ontology.SolverParameter)[0]
        steps = sol_param.get(oclass=simlammps_ontology.IntegrationTime)[0].steps
        self._engine.run(steps)
        # self._engine.write_dump("all", "atom", "atom_dump.txt")

    # OVERRIDE
    def _load_from_backend(self, uids, expired=None):
        for uid in uids:
            try:
                cuds_object = self._registry.get(uid)
            except KeyError:
                yield None

            oclass = cuds_object.oclass
            if uid == self.root:
                self._update_wrapper_from_backend(cuds_object)
            elif oclass == simlammps_ontology.Atom:
                self._update_atom_from_backend(cuds_object)
            elif oclass == simlammps_ontology.Position:
                self._update_position_from_backend(cuds_object)
            elif oclass == simlammps_ontology.Velocity:
                self._update_velocity_from_backend(cuds_object)
            elif oclass == simlammps_ontology.Force:
                self._update_force_from_backend(cuds_object)
            yield cuds_object

    def _update_wrapper_from_backend(self, wrapper):
        """
        Updates the atoms in the wrapper with the information from the engine.
        It checks if atoms were created or deleted, and updates the registry.

        Args:
            wrapper (Cuds): cuds representation of the wrapper
        """
        # TODO: Check if the number of atoms changed
        #   If a new atom was created, create its position

    def _update_atom_from_backend(self, atom):
        """
        Updates the given atom with new velocities and/or forces.

        Args:
            cuds_atom (Cuds): atom to be updated
        """
        velocity = atom.get(oclass=simlammps_ontology.Velocity)
        # The cuds atom has no velocity
        if not velocity:
            self._update_velocity_from_backend(None, atom)
        force = atom.get(oclass=simlammps_ontology.Force)
        # The cuds atom has no force
        if not force:
            self._update_force_from_backend(None, atom)

    def _update_position_from_backend(self, position, cuds_atom=None):
        """
        Updates a given position object with the latest values in the engine.

        Args:
            position (Cuds): position object to update
            cuds_atom (Cuds): atom that has said position
        """
        if cuds_atom is None:
            cuds_atom = self._parent_atom(position)
        lammps_atom = self._lammps_atom(cuds_atom)
        position.vector = lammps_atom.position

    def _update_velocity_from_backend(self, velocity, cuds_atom=None):
        """
        Updates a given velocity object with the latest values in the engine.
        If the previous cuds_velocity was None, a cuds_atom MUST be given
        (in case it has to be initialised). If there was a pre-existing value,
        the atom is not required and could be computed.

        Args:
            velocity (Cuds): velocity object to update
            cuds_atom (Cuds): atom that has said velocity
        """
        if cuds_atom is None:
            cuds_atom = self._parent_atom(velocity)
        lammps_atom = self._lammps_atom(cuds_atom)
        if velocity is not None:
            velocity.vector = lammps_atom.velocity
        # There was no velocity and now there is
        elif lammps_atom.velocity != (0, 0, 0):
            if cuds_atom is None:
                message = "Atom is required if there was no previous velocity"
                raise ValueError(message)
            velocity = simlammps_ontology.Velocity(
                vector=lammps_atom.velocity, session=self
            )
            cuds_atom.add(velocity)

    def _update_force_from_backend(self, force, cuds_atom=None):
        """
        Updates a given force object with the latest values in the engine.

        Args:
        force (Cuds): force object to update
        cuds_atom (Cuds): atom that has said force
        """
        if cuds_atom is None:
            cuds_atom = self._parent_atom(force)
        lammps_atom = self._lammps_atom(cuds_atom)
        if force is not None:
            force.vector = lammps_atom.force
        # There was no force and now there is
        elif lammps_atom.force != (0, 0, 0):
            if cuds_atom is None:
                message = "Atom is required if there was no previous force"
                raise ValueError(message)
            force = simlammps_ontology.Force(vector=lammps_atom.force, session=self)
            cuds_atom.add(force)

    # OVERRIDE
    def _apply_added(self, root_obj, buffer):
        for cuds_object in buffer.values():
            self._add_by_type(cuds_object)

    def _add_by_type(self, cuds_object):
        """
        Adds Cuds objects based on their type to the engine.

        :param cuds_object: object to add
        """
        if cuds_object.is_a(simlammps_ontology.Atom):
            self._add_atom(cuds_object)
        elif cuds_object.is_a(simlammps_ontology.Velocity):
            cuds_atom = self._parent_atom(cuds_object)
            lammps_atom = self._lammps_atom(cuds_atom)
            self._set_velocity(lammps_atom, cuds_object.vector)
        elif cuds_object.is_a(simlammps_ontology.Force):
            cuds_atom = self._parent_atom(cuds_object)
            # Lammps internal id = pylammps id + 1
            lammps_atom_id = self._atom_mapper.get(cuds_atom.uid) + 1
            self._set_force(lammps_atom_id, cuds_object.vector)
        else:
            # message = "Adding {} does not add anything to the engine."
            # (message.format(cuds_object))
            pass

    # OVERRIDE
    def _apply_updated(self, root_obj, buffer):
        for cuds_object in buffer.values():
            self._update_by_type(cuds_object)

    def _update_by_type(self, cuds_object):
        """
        Updates Cuds objects based on their type to the engine.

        Args:
            cuds_object (Cuds): object to update
        """
        # Nothing if the atom is changed (should be the pos, vel or force)
        if cuds_object.is_a(simlammps_ontology.Position):
            cuds_atom = self._parent_atom(cuds_object)
            lammps_atom = self._lammps_atom(cuds_atom)
            self._set_position(lammps_atom, cuds_object.vector)
        elif cuds_object.is_a(simlammps_ontology.Velocity):
            cuds_atom = self._parent_atom(cuds_object)
            lammps_atom = self._lammps_atom(cuds_atom)
            self._set_velocity(lammps_atom, cuds_object.vector)
        elif cuds_object.is_a(simlammps_ontology.Force):
            cuds_atom = self._parent_atom(cuds_object)
            # Lammps internal id = pylammps id + 1
            lammps_atom_id = self._atom_mapper.get(cuds_atom.uid) + 1
            self._set_force(lammps_atom_id, cuds_object.vector)
        elif (
            cuds_object.is_a(simlammps_ontology.FaceX)
            or cuds_object.is_a(simlammps_ontology.FaceY)
            or cuds_object.is_a(simlammps_ontology.FaceZ)
        ):
            box = cuds_object.get(
                rel=cuba.relationship, oclass=simlammps_ontology.SimulationBox
            )[0]
            self._update_simulation_box(box)
        else:
            # message = "Updating {} does not affect the engine."
            # print(message.format(cuds_object))
            pass

    # OVERRIDE
    def _apply_deleted(self, root_obj, buffer):
        for cuds_object in ():
            self._remove_by_type(cuds_object)

    def _remove_by_type(self, cuds_object):
        """
        Removes Cuds objects based on their type to the engine.

        Args:
            cuds_object (Cuds): object to remove
        """
        if cuds_object.is_a(simlammps_ontology.Atom):
            # Lammps internal id = pylammps id + 1
            lammps_atom_id = self._atom_mapper.get(cuds_object.uid) + 1
            self._remove_atom(lammps_atom_id)
        elif cuds_object.is_a(simlammps_ontology.Position):
            cuds_atom = self._parent_atom(cuds_object)
            lammps_atom = self._lammps_atom(cuds_atom)
            self._set_position(lammps_atom, (0, 0, 0))
        elif cuds_object.is_a(simlammps_ontology.Velocity):
            cuds_atom = self._parent_atom(cuds_object)
            lammps_atom = self._lammps_atom(cuds_atom)
            self._set_velocity(lammps_atom, (0, 0, 0))
        elif cuds_object.is_a(simlammps_ontology.Force):
            cuds_atom = self._parent_atom(cuds_object)
            # Lammps internal id = pylammps id + 1
            lammps_atom_id = self._atom_mapper.get(cuds_atom.uid) + 1
            self._set_force(lammps_atom_id, (0, 0, 0))
        elif cuds_object.is_a(simlammps_ontology.SimulationBox) or cuds_object.is_a(
            simlammps_ontology.SolverParameter
        ):
            message = "{} CANNOT be removed."
            raise TypeError(message.format(cuds_object))
        else:
            # message = "Removing {} does not affect the engine."
            # print(message.format(cuds_object))
            pass

    def _output_video(self, steps, name, width, height):
        """Saves the execution of lammps to a video.

        Args:
            steps (int): frequency for the video
            filename (string): name for the file (with extension)
            width (int): width of the video (in pixels)
            height (int): height of the video (in pixels)
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

    def _add_atom(self, atom):
        """
        Adds one atom to the engine.

        Args:
            atom (Cuds): Atom to add
        """
        material_uid = atom.get(oclass=simlammps_ontology.Material)[0].uid
        # Atom types start at 1
        atom_type = self._material_mapper.get(material_uid) + 1
        position_vector = atom.get(oclass=simlammps_ontology.Position)[0].vector

        # Position vector has x, y and z components
        self._engine.create_atoms(atom_type, "single", *position_vector)
        # Add the atom to the mapper
        lammps_atom_id = self._atom_mapper.add(atom.uid)
        lammps_atom = self._engine.atoms[lammps_atom_id]

        velocity = atom.get(oclass=simlammps_ontology.Velocity)
        if velocity:
            self._set_velocity(lammps_atom, velocity[0].vector)

        force = atom.get(oclass=simlammps_ontology.Force)
        if force:
            # Lammps internal id = pylammps id + 1
            self._set_force(lammps_atom_id + 1, force[0].vector)

    def _add_settings(self, atom_style="atomic"):
        """
        Defines the general engine settings.

        Args:
            atom_style (string):
        """
        self._engine.atom_style(atom_style)
        self._engine.atom_modify("map", "array")
        self._engine.neighbor(0.3, "bin")
        self._engine.neigh_modify("delay", 5)

    def _add_simulation_box(self, simulation_box):
        """
        Adds the simulation box to the engine.

        Args:
            simulation_box (Cuds): cuds instance of a simulation box
        """

        face_x = simulation_box.get(oclass=simlammps_ontology.FaceX)[0]
        face_y = simulation_box.get(oclass=simlammps_ontology.FaceY)[0]
        face_z = simulation_box.get(oclass=simlammps_ontology.FaceZ)[0]
        style_x = self._find_boundary_condition_style(face_x)
        style_y = self._find_boundary_condition_style(face_y)
        style_z = self._find_boundary_condition_style(face_z)

        name = simulation_box.name
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

    def _add_pair_style(self, lj):
        """
        Defines the settings for the pair style.

        Args:
            lj (Cuds): lennard-jones cuds object
        """
        if lj:
            self._engine.pair_style("lj/cut", lj.cutoffDistance)
            self._engine.pair_coeff("*", "*", lj.energyWellDepth, lj.vanDerWaalsRadius)

    def _define_fix(self, thermo=None):
        """
        Defines the fixes.
        Fixes are operations applied to the system during timestepping
        or minimization

        Args:
            thermo (Cuds): thermostat
        """
        if thermo is None:
            self._engine.fix(1, "all", "nve")
        else:
            message = "No thermostat supported yet"
            raise AttributeError(message)

    def _add_material(self, material):
        """
        Adds a material to the engine.

        Args:
            material (Cuds): Cuds representing a material
        """
        mass = material.get(oclass=simlammps_ontology.Mass)[0]
        uid = material.uid
        try:
            # Atom types start at 1
            atom_type = self._material_mapper.get(uid) + 1
        except KeyError:
            self._material_mapper.add(uid)
            atom_type = len(self._material_mapper)
        self._engine.mass(atom_type, mass.value)

    def _set_position(self, lammps_atom, position_vector):
        """
        Updates the position of an atom from LAMMPS.

        Args:
            lammps_atom (lammps atom): atom in LAMMPS
            position_vector (List[Float]): new position values
        """
        lammps_atom.position = position_vector

    def _set_velocity(self, lammps_atom, velocity_vector):
        """
        Updates the velocity of an atom from LAMMPS.

        Args:
            lammps_atom (lammps_atom): atom in LAMMPS
            velocity_vector (List[Float]): new velocity values
        """
        lammps_atom.velocity = velocity_vector

    def _set_force(self, lammps_atom_id, force_vector):
        """
        Sets the force to the atom.

        Args:
            lammps_atom_id (int): id of the atom in lammps
            force_vector (List[Float]): vector with the force values
        """
        # FIXME: Individual forces set to atoms should be made persistant
        # Add the atom to a temporal group
        self._engine.group("temp", "id", "==", lammps_atom_id)
        self._engine.fix(
            "fAtom" + str(lammps_atom_id), "temp", "setforce", *force_vector
        )
        # Delete the group
        # self._engine.group("temp", "delete")

    def _update_simulation_box(self, simulation_box):
        """
        Updates the simulation box.

        Args:
            simulation_box (Cuds): cuds of a simulation box
        """
        origin = [0, 0, 0]

        face_x = simulation_box.get(oclass=simlammps_ontology.FaceX)[0]
        face_y = simulation_box.get(oclass=simlammps_ontology.FaceY)[0]
        face_z = simulation_box.get(oclass=simlammps_ontology.FaceZ)[0]

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

    def _remove_atom(self, lammps_atom_id):
        """
        Removes an atom from LAMMPS.

        Args:
            lammps_atom_id (int): id in LAMMPS of the atom to remove
        """
        # Add the atom to a temporal group
        self._engine.group("temp", "id", "==", lammps_atom_id)
        # Remove the atoms from the group without re-assigning IDs
        self._engine.delete_atoms("group", "temp", "compress", "no")
        # Delete the group
        self._engine.group("temp", "delete")
        # Update the mapper
        self._atom_mapper.remove(lammps_atom_id)

    def _map_material(self, material):
        """
        Maps the uid of a material to a lammps atom type.

        Args:
            material (Cuds): cuds object of the material
        """
        uid = material.uid
        if uid not in self._material_mapper:
            self._material_mapper.add(uid)

    @staticmethod
    def _find_boundary_condition_style(face):
        """
        Processes face to find the style of the boundary condition.
        Can be periodic or fixed

        Args:
            face (Cuds): face of the boundary

        Returns
            string: 'p' for periodic or 'f' for fixed
        """
        # Condition can be periodic or fixed
        periodic = face.get(oclass=simlammps_ontology.Periodic)

        # Checker already makes sure there is one and only one
        if periodic is not None:
            return "p"
        return "f"

    def _parent_atom(self, cuds_object):
        """
        Gets the atom corresponding to a given cuds object.
        Mainly used to know the atom given a position, velocity...

        Args:
            cuds_object: object related to an atom

        Returns:
            Cuds: the atom
        """
        cuds_atom = cuds_object.get(
            rel=cuba.relationship, oclass=simlammps_ontology.Atom
        )[0]
        return cuds_atom

    def _lammps_atom(self, cuds_atom):
        """
        Gets the lammps atom corresponding to a given cuds atom.

        Args:
            cuds_atom (Cuds): cuds representation of an atom

        Returns:
            lammps_atom: the atom in lammps
        """
        lammps_atom_id = self._atom_mapper.get(cuds_atom.uid)
        return self._engine.atoms[lammps_atom_id]
