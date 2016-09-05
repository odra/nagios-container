#!/usr/bin/env python
from subprocess import CalledProcessError
import unittest

from resource_limits import analize, report
import nagios


class TestAnalize(unittest.TestCase):

    def runTest(self):
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {}),
            ([
                ['pod-a1b2c', 'container1', None, None, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'cpu': 0, 'memory': 0}),
            ([
                ['pod-a1b2c', 'container1', 0, 0, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'cpu': 100, 'memory': 0}),
            ([
                ['pod-a1b2c', 'container1', 100, 0, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'cpu': 0, 'memory': 100}),
            ([
                ['pod-a1b2c', 'container1', 0, 100, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'memory': 100}),
            ([
                ['pod-a1b2c', 'container1', None, 100, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'cpu': '100mi'}),
            ([
                ['pod-a1b2c', 'container1', '100mi', None, nagios.WARN],
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', {'cpu': '100mi', 'memory': '100'}),
            ([
                ['pod-a1b2c', 'container1', '100mi', '100', nagios.OK],
            ]))


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 0, nagios.WARN],
                    ['pod-a1b2c', 'container2', 100, 100, nagios.OK]
                ],
                errors=(),
            ), nagios.WARN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 0, nagios.WARN],
                    ['pod-a1b2c', 'container2', 100, 100, nagios.OK],
                    ['pod-a1b2c', 'container3', 100, 100, nagios.OK]
                ],
                errors=(),
            ), nagios.WARN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 100, nagios.OK],
                    ['pod-a1b2c', 'container2', 100, 100, nagios.OK]
                ],
                errors=(),
            ), nagios.OK)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', 100, 100, nagios.OK],
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
