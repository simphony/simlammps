"""Map an ontology individual identifier to a LAMMPS id."""

from typing import Union

from simphony_osp.utils.datatypes import Identifier


class Mapper:
    """Maps an ontology individual identifier to a LAMMPS id.

    Uses an increasing counter.
    """

    def __init__(self):
        """Constructor."""
        self._to_ontology = dict()
        self._to_lammps = dict()

    def add(self, identifier: Identifier) -> int:
        """Adds a new entry to the mapper.

        Args:
            identifier: identifier to add to the mapper.

        Raises:
            TypeError: when the given argument is not an identifier
            ValueError: when the identifier is already in the mapper.

        Returns:
            pylammps id assigned to the identifier.
        """
        if not isinstance(identifier, Identifier):
            message = "{} is not a proper identifier"
            raise TypeError(message.format(identifier))
        if identifier in self._to_lammps:
            message = "identifier {} already in the mapper"
            raise ValueError(message.format(identifier))

        lammps = len(self._to_ontology)
        self._to_ontology[lammps] = identifier
        self._to_lammps[identifier] = lammps
        return lammps

    def get(self, key: Union[int, Identifier]) -> Union[int, Identifier]:
        """Returns the equivalent lammps/ontology material id.

        Args:
            key: lammps/individual id.

        Raises:
            KeyError: when the key is not in the mapper.

        Returns:
            id mapped to the given one.
        """
        try:
            if isinstance(key, Identifier):
                return self._to_lammps[key]
            else:
                return self._to_ontology[key]
        except KeyError:
            message = "{} is a wrong id."
            raise KeyError(message.format(key))

    def remove(self, key: Union[int, Identifier]) -> None:
        """Removes the given key and the mapped id from the mapper.

        Args:
            key: id of the mapping to remove.

        Raises:
            KeyError: when the given key is not in the mapper.
        """
        try:
            if isinstance(key, Identifier):
                lammps = self._to_lammps[key]
                del self._to_lammps[key]
                del self._to_ontology[lammps]
            else:
                ontology = self._to_ontology[key]
                del self._to_ontology[key]
                del self._to_lammps[ontology]
        except KeyError:
            message = "{} is a wrong id."
            raise KeyError(message.format(key))

    def __len__(self) -> int:
        """Length of the mapping."""
        return len(self._to_ontology)

    def __contains__(self, key: Union[int, Identifier]) -> bool:
        """Containment verification."""
        if isinstance(key, Identifier):
            return key in self._to_lammps
        else:
            return key in self._to_ontology
