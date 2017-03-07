#!/usr/bin/env python
import unittest

import nagios


class TestNagios(unittest.TestCase):

    def runTest(self):
        self.assertEqual(nagios.OK, 0)
        self.assertEqual(nagios.WARN, 1)
        self.assertEqual(nagios.CRIT, 2)
        self.assertEqual(nagios.UNKNOWN, 3)


if __name__ == "__main__":
    unittest.main()
