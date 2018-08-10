#!/usr/bin/env python
from subprocess import CalledProcessError
import unittest

from disk_usage import analize, parse_df_line, parse_df_lines, report
import nagios


class TestAnalize(unittest.TestCase):

    def runTest(self):
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', [['/', 0, 0], ['/b', 15, 48]], 0, 0),
            ([
                ['pod-a1b2c', 'container1', '/', 0, 0, nagios.CRIT],
                ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.CRIT]
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', [['/', 0, 0], ['/b', 15, 48]], 20, 50),
            ([
                ['pod-a1b2c', 'container1', '/', 0, 0, nagios.OK],
                ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.WARN]
            ]))
        self.assertEqual(analize(
            'pod-a1b2c', 'container1', [['/', 0, 0], ['/b', 15, 48]], 80, 90),
            ([
                ['pod-a1b2c', 'container1', '/', 0, 0, nagios.OK],
                ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.OK]
            ]))


class TestParseDfLine(unittest.TestCase):

    def runTest(self):
        self.assertEqual(parse_df_line(
            r"Use% IUse% Mounted on"),
            ())
        self.assertEqual(parse_df_line(
            r"  1%    1% /"),
            ("/", 1, 1))
        self.assertEqual(parse_df_line(
            r"  1%    1% /run/secrets/kubernetes.io/serviceaccount"),
            ("/run/secrets/kubernetes.io/serviceaccount", 1, 1))
        self.assertEqual(parse_df_line(
            r"  1%    1% /etc/feedhenry/gitlab-shell"),
            ("/etc/feedhenry/gitlab-shell", 1, 1))


class TestParseDfLines(unittest.TestCase):

    def runTest(self):
        self.assertEqual(parse_df_lines(
            "Use% IUse% Mounted on\n"
            "  1%    1% /\n"
            "  1%    1% /run/secrets/kubernetes.io/serviceaccount\n"),
            [("/", 1, 1), ("/run/secrets/kubernetes.io/serviceaccount", 1, 1)])


class TestReport(unittest.TestCase):

    def runTest(self):
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', '/a', 0, 0, nagios.OK],
                    ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.OK]
                ],
                errors=(),
                minimum=10
            ), nagios.OK)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', '/a', 0, 0, nagios.OK],
                    ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.WARN]
                ],
                errors=(),
                minimum=10
            ), nagios.WARN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', '/a', 0, 0, nagios.CRIT],
                    ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.CRIT]
                ],
                errors=(),
                minimum=10
            ), nagios.CRIT)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', '/a', 0, 0, nagios.CRIT],
                    ['pod-a1b2c', 'container1', 'fake_unknown', 0, 0, nagios.UNKNOWN]
                ],
                errors=(),
                minimum=10
            ), nagios.UNKNOWN)
        self.assertEqual(
            report(
                results=[
                    ['pod-a1b2c', 'container1', '/a', 0, 0, nagios.OK],
                    ['pod-a1b2c', 'container1', '/b', 15, 48, nagios.OK]
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
                minimum=10
            ), nagios.UNKNOWN)


if __name__ == "__main__":
    unittest.main()

# TODO: Try to find a theoretically valid case for TestReport result of 3
# (nagios.UNKNOWN)
