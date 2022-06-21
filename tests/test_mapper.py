"""Test the SimLammps mapper utility."""

import uuid

import unittest2 as unittest

import osp.wrappers.simlammps.mapper as mapper


class TestMapper(unittest.TestCase):
    """Test the SimLammps mapper utility."""

    def test_creation(self):
        """Tests the instantiation of the mapper."""
        map = mapper.Mapper()
        self.assertFalse(map._to_cuds)
        self.assertFalse(map._to_lammps)

    def test_add(self):
        """Tests the standard, normal behaviour of the add() method."""
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        self.assertEqual(map._to_lammps, {uid: 0})
        self.assertEqual(map._to_cuds, {0: uid})

    def test_add_throws_exception(self):
        """Tests the add() method for unusual behaviours.

        - Adding an object that is already there
        - Adding an unsupported object
        """
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        self.assertRaises(ValueError, map.add, uid)
        self.assertRaises(TypeError, map.add, "key")

    def test_get(self):
        """Tests the standard, normal behaviour of the get() method."""
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        self.assertEqual(map.get(uid), 0)
        self.assertEqual(map.get(0), uid)

    def test_get_throws_exception(self):
        """Tests the get() method for unusual behaviours.

        - Getting with a wrong type
        - Getting with a key not in the mapper
        """
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        self.assertRaises(KeyError, map.get, "wrong key type")
        self.assertRaises(KeyError, map.get, 1)

    def test_remove(self):
        """Tests the standard, normal behaviour of the remove() method."""
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        # Remove by uid
        map.remove(uid)
        self.assertFalse(map._to_cuds)
        self.assertFalse(map._to_lammps)

        map.add(uid)
        # Remove by lammps id
        map.remove(0)
        self.assertFalse(map._to_cuds)
        self.assertFalse(map._to_lammps)

    def test_remove_throws_exception(self):
        """Tests the remove() method for unusual behaviours.

        - Removing with a wrong key
        - Removing something non-existent
        """
        map = mapper.Mapper()
        uid = uuid.uuid4()
        map.add(uid)

        self.assertRaises(KeyError, map.remove, "wrong key type")
        self.assertRaises(KeyError, map.remove, 1)
        self.assertRaises(KeyError, map.remove, uuid.uuid4())

    def test_contains(self):
        """Test the containment (x in Mapper)"""
        pass


if __name__ == "__main__":
    unittest.main()
