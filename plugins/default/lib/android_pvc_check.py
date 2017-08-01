#!/usr/bin/env python
import argparse
import nagios
import sys
import traceback
import openshift


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks the android-sdk Persistent Volume Claim",
    )
    parser.add_argument(
        "-p", "--project", required=False,
        help="openshift project/namespace to use",
    )
    return parser


def report(results, errors):
    if errors:
        for status, ex in errors:
            print "%s , %s" % (nagios.status_code_to_label("WARNING"), ex)
        return nagios.UNKNOWN

    for result in results:
        if result == nagios.CRIT:
            print 'AndroidSDK PersistentVolumeClaim is not Bound - Status %s' % (
                nagios.status_code_to_label(result))
            return result
        elif result == nagios.OK:
            print 'AndroidSDK PersistentVolumeClaim is Bound - Status %s' % (
                nagios.status_code_to_label(result))
            return result
        elif result == nagios.UNKNOWN:
            print 'Unable to determine the status of the AndroidSDK PersistentVolumeClaim'


def parse_response(data):
    results = []
    errors = []
    for pvc in data['items']:
        try:
            if "android-sdk" in pvc['name']:
                if "Bound" in pvc['status']['phase']:
                    results.append(nagios.OK)
                else:
                    results.append(nagios.CRIT)
            else:
                results.append(nagios.CRIT)
        except KeyError as e:
            errors.append((nagios.UNKNOWN, e))
    return results, errors


def do_request(project):
    return openshift.get_pvcs(project)


def check(project):
    if not project:
        project = openshift.get_project()
    data = do_request(project)
    results, errors = parse_response(data)
    return report(results, errors)


if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.project)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
