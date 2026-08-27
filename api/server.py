from flask import Flask, jsonify
import os
import platform
import shutil
import time

app = Flask(__name__)

START_TIME = time.time()


def get_cpu_usage():
    try:
        import psutil
        return round(psutil.cpu_percent(interval=0.5), 1)
    except Exception:
        return 0


def get_memory():
    try:
        import psutil

        memory = psutil.virtual_memory()

        return {
            "total_gb": round(memory.total / (1024 ** 3), 2),
            "used_gb": round(memory.used / (1024 ** 3), 2),
            "usage_percent": round(memory.percent, 1)
        }

    except Exception:
        return {
            "total_gb": 0,
            "used_gb": 0,
            "usage_percent": 0
        }


def get_storage():
    try:
        disk = shutil.disk_usage("/")

        total_tb = disk.total / (1024 ** 4)
        used_tb = disk.used / (1024 ** 4)

        usage_percent = (
            (disk.used / disk.total) * 100
            if disk.total
            else 0
        )

        return {
            "total_tb": round(total_tb, 2),
            "used_tb": round(used_tb, 2),
            "usage_percent": round(usage_percent, 1)
        }

    except Exception:
        return {
            "total_tb": 0,
            "used_tb": 0,
            "usage_percent": 0
        }


def get_uptime():

    seconds = int(time.time() - START_TIME)

    days = seconds // 86400
    seconds %= 86400

    hours = seconds // 3600
    seconds %= 3600

    minutes = seconds // 60

    return f"{days}d {hours}h {minutes}m"


@app.route("/api/status", methods=["GET"])
def server_status():

    memory = get_memory()
    storage = get_storage()

    return jsonify({

        "server": {

            "id": "kulzzy-server-01",

            "name": "Kulzzy Server #01",

            "status": "online",

            "environment": "production",

            "version": "1.0.0",

            "hostname": platform.node(),

            "os": platform.system(),

            "uptime": get_uptime()

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

            "memory": memory,

            "storage": storage

        },

        "services": {

            "web_server": "online",

            "database": "online",

            "storage": "online",

            "code_hub": "online",

            "radio_stream": "online"

        }

    })


@app.route("/", methods=["GET"])
def home():

    return jsonify({

        "name":
            "Kulzzy Server API",

        "server":
            "kulzzy-server-01",

        "status":
            "online",

        "version":
            "1.0.0"

    })


if __name__ == "__main__":

    app.run(
        host="0.0.0.0",
        port=5000,
        debug=False
      )
