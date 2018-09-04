#!/usr/bin/env python
############################################################################################
#
# Nagios plugin to validate pods are running on separate nodes
#
# If 2 pods from the same component are running on the same node, return a warning message
#
# Copyright (c) 2018, Red Hat Ltd. All rights reserved.
#
############################################################################################
import sys
import traceback

import nagios
import openshift


def report(issues):
    if not issues:
        print("OK: Component pod distribution as expected")
        nag_status = nagios.OK
    else:
        for issue in issues:
            print(issue)
        nag_status = nagios.WARN
    return nag_status


def check():
    issues = []
    project = openshift.get_project()
    deploymentConfigs = openshift.get_deploymentconfigs(project)
    for deploymentConfig in deploymentConfigs["items"]:
        componentName = deploymentConfig["metadata"]["name"]
        pods = openshift.get_running_pod_names(
            project, container_names=componentName)
        nodes = openshift.get_nodes_from_names(pods, project)
        if len(pods) > 1:
            for node in set(nodes):
                nodeCount = nodes.count(node)
                if nodeCount > 1:
                    issues.append("WARN: %s has %s pods running on the same node: %s" % (
                        componentName, nodeCount, node))
    return report(issues)


if __name__ == "__main__":
    code = nagios.UNKNOWN
    try:
        code = check()
    except:
        traceback.print_exc()
    finally:
        sys.exit(code)
