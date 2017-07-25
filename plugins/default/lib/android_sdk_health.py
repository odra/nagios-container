#!/usr/bin/env python
import argparse
import nagios
import sys
import traceback
import openshift


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the android-sdk pod",
    )
    parser.add_argument(
        "-p", "--project", required=False,
        help="openshift project/namespace to use",
    )
    return parser


def report(results, errors):
    if errors:
        return nagios.UNKNOWN

    for result in results:
        if result == nagios.CRIT:
            print 'Unable to contact the androidsdk - Status %s' % (
                nagios.status_code_to_label(result))
            return result
        elif result == nagios.OK:
            print 'Able to contact the androidsdk - Status %s' % (
                nagios.status_code_to_label(result))
            return result
    return nagios.UNKNOWN


def do_request(project):
    results = []
    errors = []
    pods = openshift.get_running_pod_names(project)
    command_args = ['which', 'androidctl']
    for pod in pods:
        if "android-sdk" in pod:
            command_response = openshift.exec_in_pod(project, pod, command_args)
            if "/usr/bin/androidctl" in command_response:
                results.append(nagios.OK)
            else:
                results.append(nagios.CRIT)
        else:
            results.append(nagios.CRIT)
    return results, errors


def check(project):
    if not project:
        project = openshift.get_project()
    results, error = do_request(project)
    return report(results, error)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.project)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
