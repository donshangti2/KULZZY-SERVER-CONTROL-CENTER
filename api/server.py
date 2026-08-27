from flask import (
    Flask,
    jsonify,
    request,
    send_file
)

from functools import wraps

from pathlib import Path

from secrets import compare_digest

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


app = Flask(__name__)


START_TIME = time.time()


STORAGE_ROOT = Path(
    os.environ.get(
        "KULZZY_STORAGE_ROOT",
        "/kulzzy"
    )
).resolve()


ALLOWED_AREAS = {

    "audio",

    "celebrants",

    "websites",

    "repositories",

    "uploads",

    "backups"

}


MAX_UPLOAD_SIZE = (
    500 * 1024 * 1024
)


app.config[
    "MAX_CONTENT_LENGTH"
] = MAX_UPLOAD_SIZE


# =====================================================
# API KEY
# =====================================================

API_KEY = os.environ.get(
    "KULZZY_API_KEY",
    ""
)


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
                "error":
                    "Authentication required"
            }), 401

        token = (
            authorization[7:].strip()
        )

        session = get_session(
            token
        )

        if not session:

            return jsonify({
                "error":
                    "Invalid or expired session"
            }), 401

        request.kulzzy_admin = session

        return function(
            *args,
            **kwargs
        )

    return protected


# =====================================================
# OWNER-ONLY
# =====================================================

def require_owner(function):

    @wraps(function)
    @require_auth
    def protected(
        *args,
        **kwargs
    ):

        if (
            request.kulzzy_admin["role"]
            !=
            "owner"
        ):

            return jsonify({
                "error":
                    "Owner permission required"
            }), 403

        return function(
            *args,
            **kwargs
        )

    return protected


# =====================================================
# STORAGE
# =====================================================

def safe_area(area):

    if area not in ALLOWED_AREAS:

        return None

    path = (
        STORAGE_ROOT /
        area
    ).resolve()

    if not str(path).startswith(
        str(STORAGE_ROOT) + os.sep
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

    root = safe_area(area)

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

    if not str(path).startswith(
        str(root) + os.sep
    ):

        return None

    return path


# =====================================================
# SERVER METRICS
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


def get_memory():

    try:

        import psutil

        memory = psutil.virtual_memory()

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

            "total_gb": 0,

            "used_gb": 0,

            "usage_percent": 0

        }


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

        percentage = (
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
                    percentage,
                    1
                )

        }

    except Exception:

        return {

            "total_tb": 0,

            "used_tb": 0,

            "usage_percent": 0

        }


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
# PUBLIC HEALTH CHECK
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
            "2.0.0"

    })


# =====================================================
# LOGIN
# =====================================================

@app.route(
    "/api/auth/login",
    methods=["POST"]
)
def login():

    data = request.get_json(
        silent=True
    ) or {}

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

    if not username or not password:

        return jsonify({

            "error":
                "Username and password are required."

        }), 400

    result = authenticate(
        username,
        password
    )

    if not result:

        return jsonify({

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
        authorization[7:].strip()
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
                "2.0.0",

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

        },

        "services": {

            "web_server":
                "online",

            "database":
                "online",

            "storage":
                "online",

            "code_hub":
                "online",

            "radio_stream":
                "online"

        }

    })


# =====================================================
# LIST FILES
# =====================================================

@app.route(
    "/api/files/<area>",
    methods=["GET"]
)
@require_auth
def list_files(area):

    root = safe_area(
        area
    )

    if root is None:

        return jsonify({

            "error":
                "Invalid storage area"

        }), 400

    files = []

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

    return jsonify({

        "area":
            area,

        "count":
            len(files),

        "files":
            files

    })


# =====================================================
# DOWNLOAD
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

            "error":
                "Invalid file"

        }), 400

    if not path.exists():

        return jsonify({

            "error":
                "File not found"

        }), 404

    return send_file(
        path,
        as_attachment=True
    )


# =====================================================
# UPLOAD
# =====================================================

@app.route(
    "/api/files/<area>",
    methods=["POST"]
)
@require_auth
def upload_file(area):

    root = safe_area(
        area
    )

    if root is None:

        return jsonify({

            "error":
                "Invalid storage area"

        }), 400

    if "file" not in request.files:

        return jsonify({

            "error":
                "No file supplied"

        }), 400

    uploaded = request.files[
        "file"
    ]

    if not uploaded.filename:

        return jsonify({

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

    uploaded.save(
        destination
    )

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
# DELETE
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

            "error":
                "Invalid file"

        }), 400

    if not path.exists():

        return jsonify({

            "error":
                "File not found"

        }), 404

    path.unlink()

    return jsonify({

        "success":
            True,

        "message":
            "File deleted",

        "file":
            filename

    })


# =====================================================
# FILE SIZE ERROR
# =====================================================

@app.errorhandler(
    413
)
def file_too_large(error):

    return jsonify({

        "error":
            "File exceeds the 500 MB upload limit."

    }), 413


# =====================================================
# START
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

    app.run(

        host="0.0.0.0",

        port=5000,

        debug=False

    )
