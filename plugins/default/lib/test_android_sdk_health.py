import unittest
import nagios

from android_sdk_health import report


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(report(
                results=[0],
                errors=[]
            ),
            nagios.OK
        )
        self.assertEqual(report(
                results=[2],
                errors=[]
            ),
            nagios.CRIT
        )
        self.assertEqual(report(
                results=[],
                errors=[0]
            ),
            nagios.UNKNOWN
        )
