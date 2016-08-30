#!/usr/bin/env python
import argparse
import sys
import traceback
import json
from collections import Counter

import openshift
import nagios


CPU_USAGE_DATA_FILE = 'cpu-usage-data.json'


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks container cpu usage",
    )
    parser.add_argument(
        "-w", "--warn", type=int, required=True,
        help="set warning threshold percentage",
    )
    parser.add_argument(
        "-c", "--crit", type=int, required=True,
        help="set critical threshold percentage, "
             "must be higher than or equal the warning threshold",
    )
    parser.add_argument(
        "-p", "--project", required=False,
        help="openshift project/namespace to use",
    )
    return parser


# Returns elapsed time in seconds
check_uptime_cmd = ("ps", "-p",  "1", "-o", "etimes:1=")
# Returns usage in nanoseconds
check_cpu_usage_cmd = ("cat", "/sys/fs/cgroup/cpuacct,cpu/cpuacct.usage")
# Returns quota in microseconds
check_cpu_limit_cmd = ("cat", "/sys/fs/cgroup/cpuacct,cpu/cpu.cfs_quota_us")


def get_container_cpu_usage(project, pod, container):
    usage = openshift.exec_in_pod_container(project, pod, container, check_cpu_usage_cmd)
    uptime = openshift.exec_in_pod_container(project, pod, container, check_uptime_cmd)
    limit = openshift.exec_in_pod_container(project, pod, container, check_cpu_limit_cmd)

    usage = int(usage)  # Usage in nanoseconds
    uptime = int(uptime) * 1000000000  # uptime in nanoseconds
    limit = int(limit) / 100  # Limit in millicores

    return usage, uptime, limit

# https://github.com/openshift/origin-metrics/blob/master/docs/hawkular_metrics.adoc#calculating-percentage-cpu-usage
# usage_start - usage start in nanoseconds
# usage_end - usage end in nanoseconds
# uptime_start - uptime start in nanoseconds
# uptime_end - uptime end in nanoseconds
# limit - limit set in millicores


def calculate_limit_usage(usage_start, usage_end, uptime_start, uptime_end,  limit):
    usage = usage_end - usage_start
    uptime = uptime_end - uptime_start

    core_usage = float(usage) / float(uptime)
    limit_usage = (core_usage * 1000) / limit
    limit_usage_pcent = limit_usage * 100

    return limit_usage_pcent


def read_cpu_usage():
    try:
        json_data = open(CPU_USAGE_DATA_FILE).read()
        data = json.loads(json_data)
    except IOError:
        data = {}
    return data


def write_cpu_usage(data):
    f = open(CPU_USAGE_DATA_FILE, 'w')
    f.write(json.dumps(data))
    f.close()


def analize(pod, container, prev_usage, curr_usage, prev_uptime, curr_uptime, limit,
            warning_threshold, critical_threshold):
    results = []

    if prev_usage is not None and prev_uptime is not None:
        limit_percentage = calculate_limit_usage(prev_usage, curr_usage, prev_uptime, curr_uptime, limit)

        nagios_status = nagios.UNKNOWN
        if limit_percentage >= critical_threshold:
            nagios_status = nagios.CRIT
        elif limit_percentage >= warning_threshold:
            nagios_status = nagios.WARN
        elif limit_percentage < warning_threshold:
            nagios_status = nagios.OK

        results.append([pod, container, limit_percentage, nagios_status])

    return results


def report(results, errors):
    if not results:
        return nagios.UNKNOWN

    unique_statuses = Counter(
        status
        for pod, container, usage, status in results
    )

    ret = max(unique_statuses)

    if ret == nagios.OK:
        print "%s: All %s containers are under the warning threshold" % (
            nagios.status_code_to_label(ret), len(results))
    elif ret == nagios.UNKNOWN:
        print "%s: Unable to determine usage on %s containers" % (
            nagios.status_code_to_label(ret), unique_statuses[nagios.UNKNOWN])
    elif ret == nagios.WARN:
        print "%s: There are %s containers over the warning threshold" % (
            nagios.status_code_to_label(ret), unique_statuses[nagios.WARN])
    else:
        print "%s: There are %s containers over the critical threshold and %s containers over the warning threshold" % (
            nagios.status_code_to_label(ret), unique_statuses[nagios.CRIT], unique_statuses[nagios.WARN])

    for pod, container, usage, status in results:
        print "%s: %s: - usage: %.2f%%" % (
            nagios.status_code_to_label(status), pod, usage)

    if errors:
        ret = nagios.UNKNOWN
        for pod_name, container_name, ex in errors:
            print "%s: %s:%s %s" % (
                nagios.status_code_to_label("WARNING"), pod_name, container_name, ex)

    return ret


def check(warn, crit, project):
    if crit < warn:
        msg = "critical threshold cannot be lower than warning threshold: %d < %d"
        raise ValueError(msg % (crit, warn))

    if not project:
        project = openshift.get_project()

    results = []
    errors = []

    prev_cpu_usage = read_cpu_usage()
    curr_cpu_usage = {}
    pcs = openshift.get_running_pod_containers(project)

    for pod_name, container_name, container_data in pcs:
        cpu_limit = container_data.get('resources', {}).get('limits', {}).get('cpu')
        try:
            if cpu_limit:
                curr_usage, curr_uptime, limit = get_container_cpu_usage(project, pod_name, container_name)
                curr_cpu_usage[pod_name] = {container_name: [curr_usage, curr_uptime]}
                prev_usage, prev_uptime = prev_cpu_usage.get(pod_name, {}).get(container_name, [None, None])
                results.extend(analize(pod_name, container_name, prev_usage,
                                       curr_usage, prev_uptime, curr_uptime, limit, warn, crit))
        except Exception as e:
            errors.append((pod_name, container_name, e))

    write_cpu_usage(curr_cpu_usage)
    return report(results, errors)

if __name__ == "__main__":
    args = generate_parser().parse_args()
    code = nagios.UNKNOWN
    try:
        code = check(args.warn, args.crit, args.project)
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
