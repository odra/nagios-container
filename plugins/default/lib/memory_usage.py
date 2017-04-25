#!/usr/bin/env python
import argparse
import sys
import traceback
from collections import Counter
import re

import openshift
import nagios


def generate_parser():
    parser = argparse.ArgumentParser(
        description="Checks container memory usage",
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


check_memory_usage_cmd = ("cat", "/proc/meminfo")
check_jvm_max_heap_cmd = ("java", "-XX:+PrintFlagsFinal", "-version")
check_memory_limit_cmd = ("cat", "/sys/fs/cgroup/memory/memory.limit_in_bytes")


def jvm_data(data, key):
    return re.findall(r'\s+[a-zA-Z]+\s%s\s+\:?\=\s([0-9]+)\s+\{[a-zA-Z\s?]+\}\n' % key, data)[0]


def get_meminfo_data(field, output):
    data = None
    try:
        data = int(re.findall(r"%s\:\s+([0-9]+)\skB\n" % data, output)[0])
    except IndexError:
        data = None
    finally:
        return data


def heap_thread_size(pid=1, thread_size=1024):
    folder = '/proc/%s/task' % pid
    total_tasks = len([task for task in os.listdir(folder) if task.isdigit()])
    return total_tasks * thread_size


def get_memused(data, jvm_data):
    initial =  int(jvm_data(jvm_data, 'InitialHeapSize'))
    single_thread_size = int(jvm_data(info, 'ThreadStackSize'))
    return initial + heap_thread_size(2727, thread_size=single_thread_size)


def analize(pod, container, memory_limit, memory_used, warning_threshold, critical_threshold):
    results = []
    usage = (float(memory_used) / float(memory_limit)) * 100

    nagios_status = nagios.UNKNOWN
    if usage >= critical_threshold:
        nagios_status = nagios.CRIT
    elif usage >= warning_threshold:
        nagios_status = nagios.WARN
    elif usage < warning_threshold:
        nagios_status = nagios.OK

    results.append([pod, container, int(memory_limit), int(memory_used), usage, nagios_status])
    return results


def report(results, errors):
    if not results:
        return nagios.UNKNOWN

    unique_statuses = Counter(
        status
        for pod, container, memory_total, memory_used, usage, status in results
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

    for pod, container, memory_total, memory_used, usage, status in results:
        print "%s: %s:%s: - usage: %.1f%%" % (
            nagios.status_code_to_label(status), pod, container, usage)

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

    pcs = openshift.get_running_pod_containers(project)

    for pod_name, container_name, container_data in pcs:
        memory_limit = container_data.get('resources', {}).get('limits', {}).get('memory')
        try:
            memory_usage = openshift.exec_in_pod_container(
                project, pod_name, container_name, check_memory_usage_cmd)
            jvm_heap = openshift.exec_in_pod_container(
                project, pod_name, container_name, check_jvm_max_heap_cmd)
            memory_usage = get_memused(memory_usage, jvm_heap)
            if memory_limit:
                memory_limit = openshift.exec_in_pod_container(
                    project, pod_name, container_name, check_memory_limit_cmd)
                results.extend(analize(pod_name, container_name, memory_limit, memory_usage, warn, crit))
        except Exception as e:
            errors.append((pod_name, container_name, e))

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
