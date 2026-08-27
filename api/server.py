from flask import Flask, jsonify, request, send_file
from pathlib import Path
import os
import platform
import shutil
import time
import uuid

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


MAX_UPLOAD_SIZE = 500 * 1024 * 1024

app.config["MAX_CONTENT_LENGTH"] = MAX_UPLOAD_SIZE


def safe_area(area):

    if area not in ALLOWED_AREAS:
        return None

    path = (
        STORAGE_ROOT / area
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


def safe_file(area, filename):

    root = safe_area(area)

    if root is None:
        return None

    filename = Path(filename).name

    if not filename:
        return None

    path = (
        root / filename
    ).resolve()

    if not str(path).startswith(
        str(root) + os.sep
    ):
        return None

    return path


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

        disk =
            shutil.disk_usage(
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
            "total_tb": 0,
            "used_tb": 0,
            "usage_percent": 0
        }


def get_uptime():

    seconds = int(
        time.time() -
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
            "1.1.0"

    })


@app.route(
    "/api/status",
    methods=["GET"]
)
def server_status():

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
                "1.1.0",

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


@app.route(
    "/api/files/<area>",
    methods=["GET"]
)
def list_files(area):

    root = safe_area(area)

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


@app.route(
    "/api/files/<area>/<filename>",
    methods=["GET"]
)
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


@app.route(
    "/api/files/<area>",
    methods=["POST"]
)
def upload_file(area):

    root = safe_area(area)

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

    uploaded = request.files["file"]

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
        uuid.uuid4().hex +
        extension
    )

    destination = (
        root / filename
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


@app.route(
    "/api/files/<area>/<filename>",
    methods=["DELETE"]
)
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


@app.errorhandler(
    413
)
def file_too_large(error):

    return jsonify({

        "error":
            "File exceeds the 500 MB upload limit."

    }), 413


if __name__ == "__main__":

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
