# Copyright (c) 2018, Adham Hashibon and Materials Informatics Team
# at Fraunhofer IWM.
# All rights reserved.
# Redistribution and use are limited to the scope agreed with the end user.
# No parts of this software may be used outside of this context.
# No redistribution is allowed without explicit written permission.

# Utility function and classes for the lammps wrapper


class LammpsInputScript:
    """Class for parsing a Lammps input script."""

    SECTIONS = ("Atoms", "Velocities", "Masses", "Bonds", "Pair Coeffs")

    def __init__(self, filename):
        """
        Constructor.

        :param filename: path to the input script
        """
        self._filename = filename
        self._content = None

    def parse(self):
        """
        Parses the file, loading the content.
        """
        text = self._read_clean()
        self._content = self._split_into_sections(text)

    def _read_clean(self):
        """
        Reads the file, ignoring comments

        :return loaded text as an list of lines
        """
        content = []
        with open(self._filename) as f:
            for line in f.readlines():
                line = line.partition("#")[0].strip()
                if line:
                    content.append(line)
        return content

    def _split_into_sections(self, lines):
        """
        Splits the given text into the supported sections

        :param lines: list with the lines
        """
        output = {}
        section = "Header"
        output[section] = []
        for line in lines:
            if line.endswith(self.SECTIONS):
                section = line
                output[section] = []
            else:
                output[section].append(line)
        return output

    def atom_information_generator(self):
        """
        Iterator for the positions and velocities of the atoms.

        :return an iterator of the position and velocity values
        """
        positions = self._content["Atoms"]
        velocities = self._content["Velocities"]
        for idx, line in enumerate(positions):
            pos = list(map(float, line.split()[2:5]))
            vel = list(map(float, velocities[idx].split()[1:]))
            yield pos, vel

    def box_coordinates(self):
        """
        Returns the coordinates of the box.

        :return: the coordinates (x, y, z) of the box
        """
        x, y, z = None, None, None
        for line in self._content["Header"]:
            if line.endswith("xlo xhi"):
                words = line.split()
                val = float(words[1]) - float(words[0])
                x = (val, 0, 0)
            elif line.endswith("ylo yhi"):
                words = line.split()
                val = float(words[1]) - float(words[0])
                y = (0, val, 0)
            elif line.endswith("zlo zhi"):
                words = line.split()
                val = float(words[1]) - float(words[0])
                z = (0, 0, val)
        return x, y, z
