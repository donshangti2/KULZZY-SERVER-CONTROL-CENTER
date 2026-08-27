#!/usr/bin/env python3

# =====================================================
# KULZZY SERVER CONTROL CENTER API
# VERSION 6.0.0
# =====================================================

import os
import sys
import time
import uuid
import shutil
import platform

from pathlib import Path
from functools import wraps

from flask import (
    Flask,
    jsonify,
    request,
    send_file
)


# =====================================================
# KULZZY PATHS
# =====================================================

BASE_DIR = Path(
    "/srv/kulzzy"
).resolve()


API_DIR = (
    BASE_DIR /
    "api"
)


DNS_DIR = (
    BASE_DIR /
    "dns"
)


STORAGE_ROOT = Path(
    os.environ.get(
        "KULZZY_STORAGE_ROOT",
        "/kulzzy"
    )
).resolve()


# =====================================================
# PYTHON MODULE PATHS
# =====================================================

if str(API_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(API_DIR)
    )


if str(DNS_DIR) not in sys.path:

    sys.path.insert(
        0,
        str(DNS_DIR)
    )


# =====================================================
# AUTHENTICATION
# =====================================================

from auth import (
    ensure_database,
    authenticate,
    get_session,
    revoke_session,
    cleanup_sessions
)


# =====================================================
# SERVICE MANAGER
# =====================================================

from services.service_manager import (
    service_status,
    all_services,
    perform_operation,
    service_logs
)


# =====================================================
# DEPLOYMENT
# =====================================================

from deployment import (
    deploy,
    rollback,
    health_check
)


# =====================================================
# DOMAIN MANAGER
# =====================================================

from domain_manager import (
    get_all_domains,
    get_domain,
    get_enabled_domains,
    domain_health
)


# =====================================================
# DNS MANAGER
# =====================================================

from dns_manager import (
    dns_status,
    get_records,
    configuration,
    set_server_ip
)


# =====================================================
# FLASK APPLICATION
# =====================================================

app = Flask(
    __name__
)


START_TIME = time.time()


# =====================================================
# APPLICATION SETTINGS
# =====================================================

MAX_UPLOAD_SIZE = (
    500 *
    1024 *
    1024
)


app.config[
    "MAX_CONTENT_LENGTH"
] = MAX_UPLOAD_SIZE


# =====================================================
# STORAGE AREAS
# =====================================================

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


        if not token:

            return jsonify({

                "success":
                    False,

                "error":
                    "Authentication token is missing"

            }), 401


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

        role = (
            request.kulzzy_admin.get(
                "role"
            )
        )


        if role != "owner":

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


# =====================================================
# SAFE FILE
# =====================================================

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
# CPU INFORMATION
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
# MEMORY INFORMATION
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

            "available_gb":
                round(
                    memory.available /
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

            "available_gb":
                0,

            "usage_percent":
                0

        }


# =====================================================
# STORAGE INFORMATION
# =====================================================

def get_storage():

    try:

        STORAGE_ROOT.mkdir(
            parents=True,
            exist_ok=True
        )


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


        free_tb = (
            disk.free /
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

            "free_tb":
                round(
                    free_tb,
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

            "free_tb":
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
# ROOT
# =====================================================

@app.route(
    "/",
    methods=["GET"]
)
def home():

    return jsonify({

        "success":
            True,

        "name":
            "Kulzzy Server Control Center",

        "server":
            "kulzzy-server-01",

        "status":
            "online",

        "version":
            "6.0.0",

        "message":
            "Kulzzy infrastructure API is running."

    })


# =====================================================
# API INFORMATION
# =====================================================

@app.route(
    "/api",
    methods=["GET"]
)
def api_information():

    return jsonify({

        "success":
            True,

        "name":
            "Kulzzy Server API",

        "version":
            "6.0.0",

        "status":
            "online",

        "services": [

            "authentication",

            "server-control",

            "services",

            "deployment",

            "rollback",

            "health-check",

            "domains",

            "dns",

            "storage"

        ]

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
                "6.0.0",

            "hostname":
                platform.node(),

            "os":
                platform.system(),

            "os_version":
                platform.version(),

            "architecture":
                platform.machine(),

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
# SINGLE SERVICE STATUS
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
# DOMAINS — ALL
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
# DOMAINS — ENABLED
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
# DNS STATUS
# =====================================================

@app.route(
    "/api/dns/status",
    methods=["GET"]
)
@require_auth
def dns_status_api():

    result = dns_status()


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
# DNS RECORDS
# =====================================================

@app.route(
    "/api/dns/records",
    methods=["GET"]
)
@require_auth
def dns_records_api():

    result = get_records()


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
# DNS CONFIGURATION
# =====================================================

@app.route(
    "/api/dns/configuration",
    methods=["GET"]
)
@require_auth
def dns_configuration_api():

    result = configuration()


    return jsonify(
        result
    )

# =====================================================
# SET PUBLIC IP
# =====================================================

@app.route(
    "/api/dns/public-ip",
    methods=["POST"]
)
@require_owner
def set_public_ip():

    data = (
        request.get_json(
            silent=True
        )
        or {}
    )


    public_ip = str(
        data.get(
            "ip",
            ""
        )
    ).strip()


    if not public_ip:

        return jsonify({

            "success":
                False,

            "error":
                "Public IP is required."

        }), 400


    result = set_server_ip(
        public_ip
    )


    if not result.get(
        "success",
        False
    ):

        return jsonify(
            result
        ), 400


    return jsonify(
        result
    )


# =====================================================
# DNS CONFIGURATION RELOAD
# =====================================================

@app.route(
    "/api/dns/reload",
    methods=["POST"]
)
@require_owner
def dns_reload():

    result = dns_status()


    return jsonify({

        "success":
            result.get(
                "success",
                False
            ),

        "message":
            "Kulzzy DNS configuration reloaded.",

        "dns":
            result

    })


# =====================================================
# STORAGE — LIST FILES
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

                stat = item.stat()


                files.append({

                    "name":
                        item.name,

                    "size":
                        stat.st_size,

                    "modified":
                        stat.st_mtime

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
# STORAGE — DOWNLOAD
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
# STORAGE — UPLOAD
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
            "File uploaded successfully.",

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
# STORAGE — DELETE
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
            "File deleted successfully.",

        "file":
            filename

    })


# =====================================================
# STORAGE STATUS
# =====================================================

@app.route(
    "/api/storage/status",
    methods=["GET"]
)
@require_auth
def storage_status():

    storage = get_storage()


    areas = {}


    for area in ALLOWED_AREAS:

        root = safe_area(
            area
        )


        if root is None:

            continue


        try:

            count = sum(

                1

                for item in root.iterdir()

                if item.is_file()

            )

        except Exception:

            count = 0


        areas[
            area
        ] = {

            "path":
                str(root),

            "files":
                count

        }


    return jsonify({

        "success":
            True,

        "root":
            str(STORAGE_ROOT),

        "disk":
            storage,

        "areas":
            areas

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
            "Internal server error."

    }), 500


# =====================================================
# 404
# =====================================================

@app.errorhandler(
    404
)
def not_found(
    error
):

    return jsonify({

        "success":
            False,

        "error":
            "Endpoint not found."

    }), 404


# =====================================================
# INITIALIZE STORAGE
# =====================================================

def initialize_storage():

    STORAGE_ROOT.mkdir(
        parents=True,
        exist_ok=True
    )


    for area in ALLOWED_AREAS:

        (
            STORAGE_ROOT /
            area
        ).mkdir(
            parents=True,
            exist_ok=True
        )


# =====================================================
# START SERVER
# =====================================================

if __name__ == "__main__":

    print("")
    print("==============================================")
    print("       KULZZY SERVER CONTROL CENTER")
    print("       VERSION 6.0.0")
    print("==============================================")
    print("")


    try:

        ensure_database()

    except Exception as error:

        print(
            "Database initialization warning:"
        )

        print(
            str(error)
        )


    initialize_storage()


    print(
        f"Storage: {STORAGE_ROOT}"
    )


    print(
        f"API: http://0.0.0.0:5000"
    )


    print(
        f"DNS directory: {DNS_DIR}"
    )


    print(
        "=============================================="
    )


    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )
