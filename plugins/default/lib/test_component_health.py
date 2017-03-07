#!/usr/bin/env python
import unittest

import nagios
from component_health import parse_response


class TestParseResponse(unittest.TestCase):

    def runTest(self):
        self.assertEqual(
            parse_response("{\"status\": \"ok\", \"summary\": \"Test Summary\", \"details\": []}"),
            (nagios.OK,
             'Test Summary',
             []))
        self.assertEqual(
            parse_response("{\"status\": \"warn\", \"summary\": \"Test Summary\", \"details\": []}"),
            (nagios.WARN,
             'Test Summary',
             []))
        self.assertEqual(
            parse_response("{\"status\": \"crit\", \"summary\": \"Test Summary\", \"details\": []}"),
            (nagios.CRIT,
             'Test Summary',
             []))
        self.assertEqual(
            parse_response("{\"status\": \"\", \"summary\": \"Test Summary\", \"details\": []}"),
            (nagios.UNKNOWN,
             'Test Summary',
             []))
        self.assertRaises(ValueError, parse_response, '')


if __name__ == "__main__":
    unittest.main()
