"""Test the SimLammps mapper utility."""

import unittest
import uuid

from rdflib import URIRef

from simphony_osp_simlammps.mapper import Mapper

IRI_PREFIX = "https://www.simphony-project.eu/entity#"


class TestMapper(unittest.TestCase):
    """Test the SimLammps mapper utility."""

    def test_creation(self):
        """Tests the instantiation of the mapper."""
        maper = Mapper()
        self.assertFalse(maper._to_ontology)
        self.assertFalse(maper._to_lammps)

    def test_add(self):
        """Tests the standard, normal behaviour of the add() method."""
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        self.assertEqual(mapper._to_lammps, {identifier: 0})
        self.assertEqual(mapper._to_ontology, {0: identifier})

    def test_add_throws_exception(self):
        """Tests the add() method for unusual behaviours.

        - Adding an object that is already there
        - Adding an unsupported object
        """
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        self.assertRaises(ValueError, mapper.add, identifier)
        self.assertRaises(TypeError, mapper.add, "key")

    def test_get(self):
        """Tests the standard, normal behaviour of the get() method."""
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        self.assertEqual(mapper.get(identifier), 0)
        self.assertEqual(mapper.get(0), identifier)

    def test_get_throws_exception(self):
        """Tests the get() method for unusual behaviours.

        - Getting with a wrong type
        - Getting with a key not in the mapper
        """
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        self.assertRaises(KeyError, mapper.get, "wrong key type")
        self.assertRaises(KeyError, mapper.get, 1)

    def test_remove(self):
        """Tests the standard, normal behaviour of the remove() method."""
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        # Remove by uid
        mapper.remove(identifier)
        self.assertFalse(mapper._to_ontology)
        self.assertFalse(mapper._to_lammps)

        mapper.add(identifier)
        # Remove by lammps id
        mapper.remove(0)
        self.assertFalse(mapper._to_ontology)
        self.assertFalse(mapper._to_lammps)

    def test_remove_throws_exception(self):
        """Tests the remove() method for unusual behaviours.

        - Removing with a wrong key
        - Removing something non-existent
        """
        mapper = Mapper()
        uid = uuid.uuid4()
        identifier = URIRef(IRI_PREFIX + str(uid))
        mapper.add(identifier)

        self.assertRaises(KeyError, mapper.remove, "wrong key type")
        self.assertRaises(KeyError, mapper.remove, 1)
        self.assertRaises(
            KeyError, mapper.remove, URIRef(IRI_PREFIX + str(uuid.uuid4()))
        )

    def test_contains(self):
        """Test the containment (x in Mapper)."""
        pass


if __name__ == "__main__":
    unittest.main()
