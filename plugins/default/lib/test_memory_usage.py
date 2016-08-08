#!/usr/bin/env python
from subprocess import CalledProcessError
import unittest

from memory_usage import analize, report
import nagios


class TestAnalize(unittest.TestCase):

    def runTest(self):
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 100, 0, 0),
            ([
                ['pod-a1b2c', 'container1', 100, 100, 100, nagios.CRIT],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 10, 0, 0),
            ([
                ['pod-a1b2c', 'container1', 100, 10, 10.0, nagios.CRIT],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 49, 50, 60),
            ([
                ['pod-a1b2c', 'container1', 100, 49, 49.0, nagios.OK],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 50, 50, 60),
            ([
                ['pod-a1b2c', 'container1', 100, 50, 50.0, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 59, 50, 60),
            ([
                ['pod-a1b2c', 'container1', 100, 59, 59.0, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 60, 50, 60),
            ([
                ['pod-a1b2c', 'container1', 100, 60, 60.0, nagios.CRIT],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', 100, 100, 50, 60),
            ([
                ['pod-a1b2c', 'container1', 100, 100, 100.0, nagios.CRIT],
            ]))


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 49, 49.0, nagios.OK],
                    ['pod-a1b2c', 'container2', 100, 49, 49.0, nagios.OK]
                ],
                errors=(),
            ), nagios.OK)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 49, 49.0, nagios.OK],
                    ['pod-a1b2c', 'container2', 100, 50, 50.0, nagios.WARN]
                ],
                errors=(),
            ), nagios.WARN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 49, 49.0, nagios.OK],
                    ['pod-a1b2c', 'container2', 100, 50, 50.0, nagios.WARN],
                    ['pod-a1b2c', 'container3', 100, 100, 100.0, nagios.CRIT]
                ],
                errors=(),
            ), nagios.CRIT)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 100, 100.0, nagios.CRIT],
                    ['pod-a1b2c', 'container2', 100, 100, 100.0, nagios.UNKNOWN]
                ],
                errors=(),
            ), nagios.UNKNOWN)
        self.assertEqual(
            report(
                results=[
                ],
                errors=(),
            ), nagios.UNKNOWN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 49, 49.0, nagios.OK],
                ],
                errors=(
                    (
                        'pod-a1b2c',
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
                )
            ), nagios.UNKNOWN)


if __name__ == "__main__":
    unittest.main()
