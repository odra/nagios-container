import unittest
import nagios

from ios_machine_health import report


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(report(
            results=[
                ['machine1', nagios.OK],
                ['machine2', nagios.OK]
            ],
            errors=(),
            ), nagios.OK)
        self.assertEqual(report(
            results=[
                ['machine1', nagios.OK],
                ['machine2', nagios.CRIT]
            ],
            errors=()
            ), nagios.CRIT)
        self.assertEqual(report(
            results=[
                ['machine1', nagios.OK],
                ['machine2', nagios.CRIT],
                ['machine3', nagios.UNKNOWN]
            ],
            errors=()
            ), nagios.UNKNOWN)
        self.assertEqual(report(
            results=[],
            errors=['machine1', nagios.UNKNOWN]
            ), nagios.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
