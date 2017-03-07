#!/usr/bin/env python
from subprocess import CalledProcessError
import unittest

from cpu_usage import calculate_limit_usage, analize, report
import nagios


class TestCalculateLimitUsage(unittest.TestCase):

    def runTest(self):
        self.assertEqual(calculate_limit_usage(0, 10, 0, 1000, 1000), 1.0)
        self.assertEqual(calculate_limit_usage(0, 15, 0, 1000, 1000), 1.5)
        self.assertEqual(calculate_limit_usage(0, 100, 0, 1000, 1000), 10)
        self.assertEqual(calculate_limit_usage(0, 1000, 0, 1000, 1000), 100)
        self.assertEqual(calculate_limit_usage(100, 115, 100, 1100, 1000), 1.5)
        self.assertEqual(calculate_limit_usage(100, 130, 100, 1100, 1000), 3.0)
        self.assertEqual(calculate_limit_usage(100, 130, 100, 1100, 2000), 1.5)
        self.assertEqual(calculate_limit_usage(100, 130, 100, 1100, 4000), 0.75)
        self.assertEqual(calculate_limit_usage(100, 130, 100, 1100, 500), 6.0)


class TestAnalize(unittest.TestCase):

    def runTest(self):
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 80, 90), ([['pod-a1b2c', 'container1', 10.0, nagios.OK]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 11, 20), ([['pod-a1b2c', 'container1', 10.0, nagios.OK]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 10, 20), ([['pod-a1b2c', 'container1', 10.0, nagios.WARN]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 9, 20), ([['pod-a1b2c', 'container1', 10.0, nagios.WARN]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 5, 11), ([['pod-a1b2c', 'container1', 10.0, nagios.WARN]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 5, 10), ([['pod-a1b2c', 'container1', 10.0, nagios.CRIT]]))
        self.assertEqual(analize('pod-a1b2c', 'container1', 0, 100, 0, 1000,
                                 1000, 5, 9), ([['pod-a1b2c', 'container1', 10.0, nagios.CRIT]]))


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK],
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK]
                ],
                errors=(),
            ), nagios.OK)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK],
                    ['pod-a1b2c', 'container1', 10.0, nagios.WARN]
                ],
                errors=(),
            ), nagios.WARN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK],
                    ['pod-a1b2c', 'container1', 10.0, nagios.WARN],
                    ['pod-a1b2c', 'container1', 10.0, nagios.CRIT]
                ],
                errors=(),
            ), nagios.CRIT)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK],
                    ['pod-a1b2c', 'container1', 10.0, nagios.OK]
                ],
                errors=(
                    (
                        'pod-jf02k',
                        'bad-container',
                        CalledProcessError(
                            1,
                            cmd=(
                                'oc', '-n', 'core', 'exec', 'pod-a1b2c', '-c',
                                'bad-container', '--', 'df', '--output=pcent,ipcent,target'
                            ),
                            output=(
                                "Command '('oc', '-n', 'core', 'exec', 'pod-a1b2c', '-c', 'bad-container', "
                                "'--', 'df', '--output=pcent,ipcent,target')' returned non-zero exit status 1"
                            )
                        )
                    ),
                ),
            ), nagios.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
