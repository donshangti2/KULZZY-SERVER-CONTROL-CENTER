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


ALLOWED_OPERATIONS = {
    "start",
    "stop",
    "restart",
    "logs"
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

    except subprocess.TimeoutExpired:

        return {
            "success": False,
            "output": "",
            "error": "Command timed out"
        }

    except Exception as error:

        return {
            "success": False,
            "output": "",
            "error": str(error)
        }


def validate_service(service):

    return service in SERVICES


def get_container(service):

    if not validate_service(service):

        return None

    return SERVICES[service]


def service_status(service):

    container = get_container(service)

    if not container:

        return {
            "success": False,
            "error": "Unknown service"
        }

    result = run_command([
        "docker",
        "inspect",
        "--format",
        "{{.State.Status}}",
        container
    ])

    if not result["success"]:

        return {
            "success": True,
            "service": service,
            "container": container,
            "status": "not_found"
        }

    return {
        "success": True,
        "service": service,
        "container": container,
        "status": result["output"]
    }


def all_services():

    services = {}

    for service in SERVICES:

        services[service] = \
            service_status(service)

    return services


def perform_operation(
    service,
    operation
):

    if not validate_service(service):

        return {
            "success": False,
            "error": "Unknown service"
        }

    if operation not in ALLOWED_OPERATIONS:

        return {
            "success": False,
            "error": "Operation not permitted"
        }

    container = SERVICES[service]

    command = [
        "docker",
        operation,
        container
    ]

    return run_command(command)


def service_logs(
    service,
    lines=100
):

    if not validate_service(service):

        return {
            "success": False,
            "error": "Unknown service"
        }

    try:

        lines = int(lines)

    except Exception:

        lines = 100

    lines = max(
        1,
        min(lines, 500)
    )

    container = SERVICES[service]

    return run_command([
        "docker",
        "logs",
        "--tail",
        str(lines),
        container
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
