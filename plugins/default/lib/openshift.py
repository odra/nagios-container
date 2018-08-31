import json
from subprocess import check_output, STDOUT


def oc(*args):
    return check_output(("kubectl",) + args, stderr=STDOUT)


def _get_service_selectors(oc, project, service):
    svc = json.loads(
        oc("-n", project, "get", "service", service, "-o", "json"))
    return [k + "=" + v for k, v in svc["spec"]["selector"].items()]


def get_service_selectors(project, service):
    return _get_service_selectors(oc, project, service)


def _get_pvcs(oc, project):
    return [oc("-n", project, "get", "pvc", "-o", "json")]


def get_pvcs(project):
    return _get_pvcs(oc, project)


def _get_running_pod_names(oc, project, selector=None, container_names=None):
    # Manually filter Running pods because of a bug in `oc get`, see:
    # https://github.com/kubernetes/kubernetes/issues/29115
    args = ("-n", project, "get", "pods", "-o", "json")

    if selector:
        args += ("--selector=" + ",".join(selector),)

    pods = json.loads(oc(*args))["items"]

    if container_names:
        pods = [p for p in pods for c in p["spec"]
                ["containers"] if c["name"] in container_names]

    return [p["metadata"]["name"] for p in pods if p["status"]["phase"] == "Running"]


def get_running_pod_names(project, selector=None, container_names=None):
    return _get_running_pod_names(oc, project, selector, container_names)


def _get_nodes_from_names(pods, project):
    nodes = []
    for pod in pods:
        nodes.append(json.loads(
            oc("get", "pods", pod, "-o", "json", "-n", project))["spec"]["nodeName"])
    return nodes


def get_nodes_from_names(pods, project):
    return _get_nodes_from_names(pods, project)


def _get_deploymentconfigs(oc, project):
    return json.loads(oc("-n", project, "get", "dc", "-o", "json"))


def get_deploymentconfigs(project):
    return _get_deploymentconfigs(oc, project)


def _exec_in_pods(oc, project, pods, cmd):
    return [oc("-n", project, "exec", name, "--", *cmd) for name in pods]


def exec_in_pods(project, pods, cmd):
    return _exec_in_pods(oc, project, pods, cmd)


def _exec_in_pod(oc, project, pod, cmd):
    return oc("-n", project, "exec", pod, "--", *cmd)


def exec_in_pod(project, pod, cmd):
    return _exec_in_pod(oc, project, pod, cmd)


def _exec_in_pod_container(oc, project, pod, container, cmd):
    return oc("-n", project, "exec", pod, "-c", container, "--", *cmd)


def exec_in_pod_container(project, pod, container, cmd):
    return _exec_in_pod_container(oc, project, pod, container, cmd)


def _get_running_pod_containers(oc, project, selector=None, container_names=None):
    # Changed param from "--show-all=false" to "--show-all=true" due to changes in oc client
    args = ("-n", project, "get", "pods", "--show-all=true", "-o", "json")

    if selector:
        args += ("--selector=" + ",".join(selector),)

    pods = json.loads(oc(*args))["items"]

    result = []
    for p in pods:
        if p["status"]["phase"] == "Running":
            for c in p["spec"]["containers"]:
                if (not container_names or c["name"] in container_names):
                    result.append((p["metadata"]["name"], c["name"], c))

    return result

    # Technically, all of the above could be done in one shot, but its too hard to read
    # return list(itertools.chain.from_iterable(
    #     [[(p["metadata"]["name"], c["name"]) for c in p["spec"]["containers"]]
    #         for p in pods if p["status"]["phase"] == "Running"]
    # ))


def get_running_pod_containers(project, selector=None, container_names=None):
    return _get_running_pod_containers(oc, project, selector)


def get_config_maps(project):
    args = ("-n", project, "get", "configmap", "-o", "json")

    config_maps = json.loads(oc(*args))["items"]

    return {config_map["metadata"]["name"]: config_map["data"] for config_map in config_maps}


def _get_container_env(project, pod, container):
    config_maps = get_config_maps(project)

    env_dict = {}

    pod = json.loads(oc(*("-n", project, "get", "pod", pod, "-o", "json")))

    for c in [c for c in pod["spec"]["containers"] if (c["name"] == container)]:
        for e in c["env"]:
            env_value = None
            if "value" in e:
                env_value = e["value"]
            elif "valueFrom" in e:
                try:
                    key_ref = e["valueFrom"]["configMapKeyRef"]
                    env_value = config_maps[key_ref["name"]][key_ref["key"]]
                except:
                    pass

                # using try/catch seems cleaner than:
                # if key_ref["name"] in config_maps and key_ref["key"] in config_maps[key_ref["name"]]:
                #     env_value = config_maps[key_ref["name"]][key_ref["key"]]

            if env_value:
                env_dict[e["name"]] = env_value

    return env_dict


def get_container_env(project, pod, container):
    return _get_container_env(project, pod, container)


def get_project():
    with open("/var/run/secrets/kubernetes.io/serviceaccount/namespace") as f:
        data = f.read().rstrip("\n")
    return data
