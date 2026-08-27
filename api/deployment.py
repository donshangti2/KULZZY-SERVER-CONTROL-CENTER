import subprocess
from pathlib import Path


PROJECT_ROOT = Path(
    "/srv/kulzzy"
)


DEPLOY_SCRIPT = (
    PROJECT_ROOT /
    "deploy" /
    "deploy.sh"
)


ROLLBACK_SCRIPT = (
    PROJECT_ROOT /
    "deploy" /
    "rollback.sh"
)


HEALTH_SCRIPT = (
    PROJECT_ROOT /
    "deploy" /
    "health-check.sh"
)


def run_script(script):

    if not script.exists():

        return {
            "success": False,
            "error":
                f"Script not found: {script}"
        }


    try:

        result = subprocess.run(

            [
                "bash",
                str(script)
            ],

            cwd=str(
                PROJECT_ROOT
            ),

            capture_output=True,

            text=True,

            timeout=300

        )


        return {

            "success":
                result.returncode == 0,

            "exit_code":
                result.returncode,

            "output":
                result.stdout,

            "error":
                result.stderr

        }


    except subprocess.TimeoutExpired:

        return {

            "success": False,

            "error":
                "Deployment timed out."

        }


    except Exception as error:

        return {

            "success": False,

            "error":
                str(error)

        }


def deploy():

    return run_script(
        DEPLOY_SCRIPT
    )


def rollback():

    return run_script(
        ROLLBACK_SCRIPT
    )


def health_check():

    return run_script(
        HEALTH_SCRIPT
      )
