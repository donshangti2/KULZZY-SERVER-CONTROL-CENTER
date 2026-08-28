#!/usr/bin/env python3

# =====================================================
# KULZZY DNS DIAGNOSTICS
# VERSION 1.0
# =====================================================

import socket
import subprocess

from pathlib import Path


# =====================================================
# CONFIGURATION
# =====================================================

BASE_DIR = Path(
    "/srv/kulzzy"
)

DNS_SERVER = (
    "127.0.0.1"
)

DNS_PORT = 53


# =====================================================
# SERVICE STATUS
# =====================================================

def service_status():

    try:

        result = subprocess.run(

            [
                "systemctl",
                "is-active",
                "kulzzy-dns.service"
            ],

            capture_output=True,

            text=True,

            timeout=5

        )


        status = (
            result.stdout
            .strip()
        )


        return {

            "success":
                True,

            "service":
                "kulzzy-dns.service",

            "status":
                status,

            "active":
                status == "active"

        }


    except Exception as error:

        return {

            "success":
                False,

            "error":
                str(error)

        }


# =====================================================
# DNS PORT CHECK
# =====================================================

def port_check():

    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    sock.settimeout(
        2
    )


    try:

        sock.connect(
            (
                DNS_SERVER,
                DNS_PORT
            )
        )


        return {

            "success":
                True,

            "host":
                DNS_SERVER,

            "port":
                DNS_PORT,

            "reachable":
                True

        }


    except Exception as error:

        return {

            "success":
                True,

            "host":
                DNS_SERVER,

            "port":
                DNS_PORT,

            "reachable":
                False,

            "error":
                str(error)

        }


    finally:

        sock.close()


# =====================================================
# DNS DIAGNOSTICS
# =====================================================

def diagnostics():

    service = service_status()

    port = port_check()


    return {

        "success":
            True,

        "service":
            service,

        "port":
            port

    }


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    import json


    print(
        json.dumps(
            diagnostics(),
            indent=4
        )
)
