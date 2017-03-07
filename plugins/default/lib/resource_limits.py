#!/usr/bin/env python
import argparse
import sys
import traceback
from collections import Counter

import openshift
import nagios


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks container resource limits are set for cpu and memory", )
    parser.add_argument(
        "-p", "--project", required=False,
        help="openshift project/namespace to use",
    )
    return parser


def analize(pod, container, resource_limits):
    results = []

    cpu_limit = resource_limits.get('cpu', None)
    mem_limit = resource_limits.get('memory', None)

    if cpu_limit and mem_limit:
        nagios_status = nagios.OK
    else:
        nagios_status = nagios.WARN

    results.append([pod, container, cpu_limit, mem_limit, nagios_status])
    return results


def report(results, errors):
    if not results:
        return nagios.UNKNOWN

    unique_statuses = Counter(
        status
        for pod, container, cpu_limit, mem_limit, status in results
    )

    ret = max(unique_statuses)

    if ret == nagios.OK:
        print "%s: All %s containers have memory and cpu limits set" % (
            nagios.status_code_to_label(ret), len(results))
    elif ret == nagios.UNKNOWN:
        print "%s: Unable to determine cpu and memory limits on %s containers" % (
            nagios.status_code_to_label(ret), unique_statuses[nagios.UNKNOWN])
    elif ret == nagios.WARN:
        print "%s: There are %s containers that do not have both a cpu and memory limit set" % (
            nagios.status_code_to_label(ret), unique_statuses[nagios.WARN])

    for pod, container, cpu_limit, mem_limit, status in results:
        print "%s: %s:%s: - memory limit: %s - cpu limit: %s" % (
            nagios.status_code_to_label(status), pod, container, mem_limit, cpu_limit)

    if errors:
        ret = nagios.UNKNOWN
        for pod_name, container_name, ex in errors:
            print "%s: %s:%s %s" % (
                nagios.status_code_to_label("WARNING"), pod_name, container_name, ex)

    return ret


def check(project):
    if not project:
        project = openshift.get_project()

    results = []
    errors = []

    pcs = openshift.get_running_pod_containers(project)

    for pod_name, container_name, container_data in pcs:
        resource_limits = container_data.get('resources', {}).get('limits', {})
        try:
            results.extend(analize(pod_name, container_name, resource_limits))
        except Exception as e:
            errors.append((pod_name, container_name, e))

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
