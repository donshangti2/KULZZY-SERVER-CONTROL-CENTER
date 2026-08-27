from flask import (
    Flask,
    jsonify,
    request,
    send_file
)

from functools import wraps
from pathlib import Path

import os
import platform
import shutil
import time
import uuid


from auth import (
    ensure_database,
    authenticate,
    get_session,
    revoke_session,
    cleanup_sessions
)


from services.service_manager import (
    service_status,
    all_services,
    perform_operation,
    service_logs
)


from deployment import (
    deploy,
    rollback,
    health_check
)


from domain_manager import (
    get_all_domains,
    get_domain,
    get_enabled_domains,
    domain_health
)


# =====================================================
# KULZZY SERVER API
# VERSION 5.0.0
# =====================================================

app = Flask(__name__)

START_TIME = time.time()


STORAGE_ROOT = Path(
    os.environ.get(
        "KULZZY_STORAGE_ROOT",
        "/kulzzy"
    )
).resolve()


MAX_UPLOAD_SIZE = (
    500 *
    1024 *
    1024
)


app.config[
    "MAX_CONTENT_LENGTH"
] = MAX_UPLOAD_SIZE


ALLOWED_AREAS = {

    "audio",

    "celebrants",

    "websites",

    "repositories",

    "uploads",

    "backups"

}


# =====================================================
# AUTHENTICATION
# =====================================================

def require_auth(function):

    @wraps(function)
    def protected(
        *args,
        **kwargs
    ):

        authorization = (
            request.headers.get(
                "Authorization",
                ""
            )
        )


        if not authorization.startswith(
            "Bearer "
        ):

            return jsonify({

                "success":
                    False,

                "error":
                    "Authentication required"

            }), 401


        token = (
            authorization[7:]
            .strip()
        )


        session = get_session(
            token
        )


        if not session:

            return jsonify({

                "success":
                    False,

                "error":
                    "Invalid or expired session"

            }), 401


        request.kulzzy_admin = (
            session
        )


        return function(
            *args,
            **kwargs
        )


    return protected


# =====================================================
# OWNER AUTHENTICATION
# =====================================================

def require_owner(function):

    @wraps(function)
    @require_auth
    def protected(
        *args,
        **kwargs
    ):

        if request.kulzzy_admin.get(
            "role"
        ) != "owner":

            return jsonify({

                "success":
                    False,

                "error":
                    "Owner permission required"

            }), 403


        return function(
            *args,
            **kwargs
        )


    return protected


# =====================================================
# STORAGE SECURITY
# =====================================================

def safe_area(
    area
):

    if area not in ALLOWED_AREAS:

        return None


    path = (
        STORAGE_ROOT /
        area
    ).resolve()


    root_string = (
        str(STORAGE_ROOT)
        +
        os.sep
    )


    if not str(
        path
    ).startswith(
        root_string
    ):

        return None


    path.mkdir(
        parents=True,
        exist_ok=True
    )


    return path


def safe_file(
    area,
    filename
):

    root = safe_area(
        area
    )


    if root is None:

        return None


    filename = Path(
        filename
    ).name


    if not filename:

        return None


    path = (
        root /
        filename
    ).resolve()


    root_string = (
        str(root)
        +
        os.sep
    )


    if not str(
        path
    ).startswith(
        root_string
    ):

        return None


    return path


# =====================================================
# CPU
# =====================================================

def get_cpu_usage():

    try:

        import psutil

        return round(
            psutil.cpu_percent(
                interval=0.5
            ),
            1
        )

    except Exception:

        return 0


# =====================================================
# MEMORY
# =====================================================

def get_memory():

    try:

        import psutil

        memory = (
            psutil.virtual_memory()
        )


        return {

            "total_gb":
                round(
                    memory.total /
                    (1024 ** 3),
                    2
                ),

            "used_gb":
                round(
                    memory.used /
                    (1024 ** 3),
                    2
                ),

            "usage_percent":
                round(
                    memory.percent,
                    1
                )

        }


    except Exception:

        return {

            "total_gb":
                0,

            "used_gb":
                0,

            "usage_percent":
                0

        }


# =====================================================
# STORAGE
# =====================================================

def get_storage():

    try:

        disk = shutil.disk_usage(
            STORAGE_ROOT
        )


        total_tb = (
            disk.total /
            (1024 ** 4)
        )


        used_tb = (
            disk.used /
            (1024 ** 4)
        )


        usage_percent = (
            disk.used /
            disk.total *
            100
        )


        return {

            "total_tb":
                round(
                    total_tb,
                    2
                ),

            "used_tb":
                round(
                    used_tb,
                    2
                ),

            "usage_percent":
                round(
                    usage_percent,
                    1
                )

        }


    except Exception:

        return {

            "total_tb":
                0,

            "used_tb":
                0,

            "usage_percent":
                0

        }


# =====================================================
# UPTIME
# =====================================================

def get_uptime():

    seconds = int(
        time.time()
        -
        START_TIME
    )


    days = (
        seconds //
        86400
    )


    seconds %= 86400


    hours = (
        seconds //
        3600
    )


    seconds %= 3600


    minutes = (
        seconds //
        60
    )


    return (
        f"{days}d "
        f"{hours}h "
        f"{minutes}m"
    )


# =====================================================
# HOME
# =====================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({

        "name":
            "Kulzzy Server API",

        "server":
            "kulzzy-server-01",

        "status":
            "online",

        "version":
            "5.0.0"

    })


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    username = str(
        data.get(
            "username",
            ""
        )
    ).strip()


    password = str(
        data.get(
            "password",
            ""
        )
    )


    if (
        not username
        or
        not password
    ):

        return jsonify({

            "success":
                False,

            "error":
                "Username and password are required."

        }), 400


    result = authenticate(
        username,
        password
    )


    if not result:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid username or password."

        }), 401


    return jsonify({

        "success":
            True,

        "session":
            result

    })


# =====================================================
# LOGOUT
# =====================================================

@app.route(
    "/api/auth/logout",
    methods=["POST"]
)
@require_auth
def logout():

    authorization = (
        request.headers.get(
            "Authorization",
            ""
        )
    )


    token = (
        authorization[7:]
        .strip()
    )


    revoke_session(
        token
    )


    return jsonify({

        "success":
            True,

        "message":
            "Logged out successfully."

    })


# =====================================================
# CURRENT ADMIN
# =====================================================

@app.route(
    "/api/auth/me",
    methods=["GET"]
)
@require_auth
def current_admin():

    return jsonify({

        "success":
            True,

        "authenticated":
            True,

        "admin":
            request.kulzzy_admin

    })


# =====================================================
# SERVER STATUS
# =====================================================

@app.route(
    "/api/status",
    methods=["GET"]
)
@require_auth
def server_status():

    cleanup_sessions()


    memory = get_memory()

    storage = get_storage()


    return jsonify({

        "success":
            True,

        "server": {

            "id":
                "kulzzy-server-01",

            "name":
                "Kulzzy Server #01",

            "status":
                "online",

            "environment":
                "production",

            "version":
                "5.0.0",

            "hostname":
                platform.node(),

            "os":
                platform.system(),

            "uptime":
                get_uptime()

        },


        "hardware": {

            "cpu": {

                "model":
                    platform.processor(),

                "cores":
                    os.cpu_count(),

                "threads":
                    os.cpu_count(),

                "usage_percent":
                    get_cpu_usage()

            },


            "memory":
                memory,


            "storage":
                storage

        }

    })


# =====================================================
# ALL SERVICES
# =====================================================

@app.route(
    "/api/services",
    methods=["GET"]
)
@require_auth
def services_status():

    return jsonify({

        "success":
            True,

        "services":
            all_services()

    })


# =====================================================
# SINGLE SERVICE
# =====================================================

@app.route(
    "/api/services/<service>",
    methods=["GET"]
)
@require_auth
def single_service_status(
    service
):

    result = service_status(
        service
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 404


    return jsonify(
        result
    )


# =====================================================
# START SERVICE
# =====================================================

@app.route(
    "/api/services/<service>/start",
    methods=["POST"]
)
@require_owner
def start_service(
    service
):

    result = perform_operation(
        service,
        "start"
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 400


    return jsonify({

        "success":
            True,

        "service":
            service,

        "operation":
            "start",

        "result":
            result

    })


# =====================================================
# STOP SERVICE
# =====================================================

@app.route(
    "/api/services/<service>/stop",
    methods=["POST"]
)
@require_owner
def stop_service(
    service
):

    result = perform_operation(
        service,
        "stop"
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 400


    return jsonify({

        "success":
            True,

        "service":
            service,

        "operation":
            "stop",

        "result":
            result

    })


# =====================================================
# RESTART SERVICE
# =====================================================

@app.route(
    "/api/services/<service>/restart",
    methods=["POST"]
)
@require_owner
def restart_service(
    service
):

    result = perform_operation(
        service,
        "restart"
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 400


    return jsonify({

        "success":
            True,

        "service":
            service,

        "operation":
            "restart",

        "result":
            result

    })


# =====================================================
# SERVICE LOGS
# =====================================================

@app.route(
    "/api/services/<service>/logs",
    methods=["GET"]
)
@require_auth
def logs(
    service
):

    lines = request.args.get(
        "lines",
        "100"
    )


    result = service_logs(
        service,
        lines
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 400


    return jsonify({

        "success":
            True,

        "service":
            service,

        "logs":
            result.get(
                "output",
                ""
            )

    })


# =====================================================
# DEPLOYMENT
# =====================================================

@app.route(
    "/api/deploy",
    methods=["POST"]
)
@require_owner
def deploy_server():

    result = deploy()


    status_code = (

        200

        if result.get(
            "success"
        )

        else

        500

    )


    return jsonify(
        result
    ), status_code


# =====================================================
# ROLLBACK
# =====================================================

@app.route(
    "/api/rollback",
    methods=["POST"]
)
@require_owner
def rollback_server():

    result = rollback()


    status_code = (

        200

        if result.get(
            "success"
        )

        else

        500

    )


    return jsonify(
        result
    ), status_code


# =====================================================
# HEALTH CHECK
# =====================================================

@app.route(
    "/api/health-check",
    methods=["GET"]
)
@require_auth
def server_health_check():

    result = health_check()


    status_code = (

        200

        if result.get(
            "success"
        )

        else

        500

    )


    return jsonify(
        result
    ), status_code


# =====================================================
# DOMAIN — ALL
# =====================================================

@app.route(
    "/api/domains",
    methods=["GET"]
)
@require_auth
def domains():

    result = get_all_domains()


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 500


    return jsonify(
        result
    )


# =====================================================
# DOMAIN — ENABLED
# =====================================================

@app.route(
    "/api/domains/enabled",
    methods=["GET"]
)
@require_auth
def enabled_domains():

    result = get_enabled_domains()


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 500


    return jsonify(
        result
    )


# =====================================================
# DOMAIN — SINGLE
# =====================================================

@app.route(
    "/api/domains/<path:hostname>",
    methods=["GET"]
)
@require_auth
def single_domain(
    hostname
):

    result = get_domain(
        hostname
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 404


    return jsonify(
        result
    )


# =====================================================
# DOMAIN HEALTH
# =====================================================

@app.route(
    "/api/domain-health",
    methods=["GET"]
)
@require_auth
def domain_health_status():

    result = domain_health()


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 500


    return jsonify(
        result
    )


# =====================================================
# LIST FILES
# =====================================================

@app.route(
    "/api/files/<area>",
    methods=["GET"]
)
@require_auth
def list_files(
    area
):

    root = safe_area(
        area
    )


    if root is None:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid storage area"

        }), 400


    files = []


    try:

        for item in root.iterdir():

            if item.is_file():

                files.append({

                    "name":
                        item.name,

                    "size":
                        item.stat().st_size,

                    "modified":
                        item.stat().st_mtime

                })


    except Exception as error:

        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500


    return jsonify({

        "success":
            True,

        "area":
            area,

        "count":
            len(files),

        "files":
            files

    })


# =====================================================
# DOWNLOAD FILE
# =====================================================

@app.route(
    "/api/files/<area>/<filename>",
    methods=["GET"]
)
@require_auth
def download_file(
    area,
    filename
):

    path = safe_file(
        area,
        filename
    )


    if path is None:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid file"

        }), 400


    if not path.exists():

        return jsonify({

            "success":
                False,

            "error":
                "File not found"

        }), 404


    return send_file(
        path,
        as_attachment=True
    )


# =====================================================
# UPLOAD FILE
# =====================================================

@app.route(
    "/api/files/<area>",
    methods=["POST"]
)
@require_auth
def upload_file(
    area
):

    root = safe_area(
        area
    )


    if root is None:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid storage area"

        }), 400


    if "file" not in request.files:

        return jsonify({

            "success":
                False,

            "error":
                "No file supplied"

        }), 400


    uploaded = request.files[
        "file"
    ]


    if not uploaded.filename:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid filename"

        }), 400


    original_name = Path(
        uploaded.filename
    ).name


    extension = (
        Path(
            original_name
        ).suffix
        .lower()
    )


    filename = (
        uuid.uuid4().hex
        +
        extension
    )


    destination = (
        root /
        filename
    )


    try:

        uploaded.save(
            destination
        )


    except Exception as error:

        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500


    return jsonify({

        "success":
            True,

        "message":
            "File uploaded",

        "original_name":
            original_name,

        "stored_name":
            filename,

        "area":
            area,

        "size":
            destination.stat().st_size

    }), 201


# =====================================================
# DELETE FILE
# =====================================================

@app.route(
    "/api/files/<area>/<filename>",
    methods=["DELETE"]
)
@require_owner
def delete_file(
    area,
    filename
):

    path = safe_file(
        area,
        filename
    )


    if path is None:

        return jsonify({

            "success":
                False,

            "error":
                "Invalid file"

        }), 400


    if not path.exists():

        return jsonify({

            "success":
                False,

            "error":
                "File not found"

        }), 404


    try:

        path.unlink()


    except Exception as error:

        return jsonify({

            "success":
                False,

            "error":
                str(error)

        }), 500


    return jsonify({

        "success":
            True,

        "message":
            "File deleted",

        "file":
            filename

    })


# =====================================================
# FILE TOO LARGE
# =====================================================

@app.errorhandler(
    413
)
def file_too_large(
    error
):

    return jsonify({

        "success":
            False,

        "error":
            "File exceeds the 500 MB upload limit."

    }), 413


# =====================================================
# GENERAL ERROR
# =====================================================

@app.errorhandler(
    500
)
def internal_error(
    error
):

    return jsonify({

        "success":
            False,

        "error":
            "Internal server error"

    }), 500


# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":

    ensure_database()


    for area in ALLOWED_AREAS:

        (
            STORAGE_ROOT /
            area
        ).mkdir(
            parents=True,
            exist_ok=True
        )


    print(
        "========================================"
    )


    print(
        "       KULZZY SERVER API"
    )


    print(
        "       VERSION 5.0.0"
    )


    print(
        "========================================"
    )


    print(
        f"Storage: {STORAGE_ROOT}"
    )


    print(
        "API: http://0.0.0.0:5000"
    )


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )
