import subprocess
import json
from datetime import datetime, timezone


SERVICES = {
    "api": "kulzzy-server-api",
    "database": "kulzzy-database",
    "storage": "kulzzy-storage",
    "code_hub": "kulzzy-code-hub",
    "website": "kulzzy-web",
    "radio": "kulzzy-radio"
}


def run_command(command):

    try:

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=30
        )

        return {
            "success":
                result.returncode == 0,

            "output":
                result.stdout.strip(),

            "error":
                result.stderr.strip()
        }

    except Exception as error:

        return {
            "success": False,
            "output": "",
            "error": str(error)
        }


def service_status(service):

    if service not in SERVICES:

        return {
            "success": False,
            "error": "Unknown service"
        }

    container = SERVICES[service]

    result = run_command([
        "docker",
        "inspect",
        "--format",
        "{{.State.Status}}",
        container
    ])

    if not result["success"]:

        return {
            "service": service,
            "container": container,
            "status": "not_found"
        }

    return {
        "service": service,
        "container": container,
        "status": result["output"]
    }


def all_services():

    result = {}

    for service in SERVICES:

        result[service] = service_status(
            service
        )

    return result


def start_service(service):

    if service not in SERVICES:

        return {
            "success": False,
            "error": "Unknown service"
        }

    return run_command([
        "docker",
        "start",
        SERVICES[service]
    ])


def stop_service(service):

    if service not in SERVICES:

        return {
            "success": False,
            "error": "Unknown service"
        }

    return run_command([
        "docker",
        "stop",
        SERVICES[service]
    ])


def restart_service(service):

    if service not in SERVICES:

        return {
            "success": False,
            "error": "Unknown service"
        }

    return run_command([
        "docker",
        "restart",
        SERVICES[service]
    ])


def service_logs(
    service,
    lines=100
):

    if service not in SERVICES:

        return {
            "success": False,
            "error": "Unknown service"
        }

    return run_command([
        "docker",
        "logs",
        "--tail",
        str(lines),
        SERVICES[service]
    ])


def service_summary():

    return {

        "generated_at":
            datetime.now(
                timezone.utc
            ).isoformat(),

        "services":
            all_services()

    }


if __name__ == "__main__":

    print(
        json.dumps(
            service_summary(),
            indent=2
        )
  )
