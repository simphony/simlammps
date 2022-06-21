from uuid import UUID


class Mapper:
    """
    Maps a CUDS uid to a LAMMPS id (increasing counter).
    """

    def __init__(self):
        """Constructor."""
        self._to_cuds = dict()
        self._to_lammps = dict()

    def add(self, cuds_uid):
        """Adds a new entry to the mapper.

        Args:
            cuds_uid (uuid.UUID): uid to add to the mapper

        Raises:
            TypeError: when the given argument is not a uuid
            ValueError: when the uid is already in the mapper

        Returns:
            int: pylammps id assigned to the cuds_uid
        """
        if not isinstance(cuds_uid, UUID):
            message = "{} is not a proper uuid"
            raise TypeError(message.format(cuds_uid))
        if cuds_uid in self._to_lammps:
            message = "uid {} already in the mapper"
            raise ValueError(message.format(cuds_uid))

        lammps = len(self._to_cuds)
        self._to_cuds[lammps] = cuds_uid
        self._to_lammps[cuds_uid] = lammps
        return lammps

    def get(self, key):
        """Returns the equivalent lammps/cuds material id.

        Args:
            key (int/UUID): lammps/cuds id

        Raises:
            KeyError: when the key is not in the mapper

        Returns:
            int/UUID: id mapped to the given one
        """
        try:
            if isinstance(key, UUID):
                return self._to_lammps[key]
            else:
                return self._to_cuds[key]
        except KeyError:
            message = "{} is a wrong id."
            raise KeyError(message.format(key))

    def remove(self, key):
        """Removes the given key and the mapped id from the mapper

        Args:
            key (int/UUID): id of the mapping to remove

        Raises:
            KeyError: when the given key is not in the mapper
        """
        try:
            if isinstance(key, UUID):
                lammps = self._to_lammps[key]
                del self._to_lammps[key]
                del self._to_cuds[lammps]
            else:
                cuds = self._to_cuds[key]
                del self._to_cuds[key]
                del self._to_lammps[cuds]
        except KeyError:
            message = "{} is a wrong id."
            raise KeyError(message.format(key))

    def __len__(self):
        return len(self._to_cuds)

    def __contains__(self, key):
        if isinstance(key, UUID):
            return key in self._to_lammps
        else:
            return key in self._to_cuds
