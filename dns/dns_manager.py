#!/usr/bin/env python3

# =====================================================
# KULZZY DNS MANAGER
# VERSION 1.0
# =====================================================

import json
import re
from pathlib import Path


# =====================================================
# PATHS
# =====================================================

BASE_DIR = Path(
    "/srv/kulzzy"
)

DNS_DIR = (
    BASE_DIR /
    "dns"
)

ZONE_DIR = (
    DNS_DIR /
    "zones"
)

ZONE_FILE = (
    ZONE_DIR /
    "kulzzyradio.com.zone"
)


# =====================================================
# DOMAIN
# =====================================================

PRIMARY_DOMAIN = (
    "kulzzyradio.com"
)


# =====================================================
# DNS RECORD TYPES
# =====================================================

ALLOWED_RECORD_TYPES = {

    "A",
    "AAAA",
    "CNAME",
    "MX",
    "TXT",
    "NS"

}


# =====================================================
# DIRECTORY SETUP
# =====================================================

def ensure_dns_directories():

    ZONE_DIR.mkdir(
        parents=True,
        exist_ok=True
    )


# =====================================================
# LOAD ZONE
# =====================================================

def load_zone():

    ensure_dns_directories()


    if not ZONE_FILE.exists():

        return {

            "success":
                False,

            "error":
                "DNS zone file not found.",

            "file":
                str(ZONE_FILE)

        }


    try:

        content = ZONE_FILE.read_text(
            encoding="utf-8"
        )


        return {

            "success":
                True,

            "domain":
                PRIMARY_DOMAIN,

            "file":
                str(ZONE_FILE),

            "content":
                content

        }


    except Exception as error:

        return {

            "success":
                False,

            "error":
                str(error)

        }


# =====================================================
# VALIDATE IP
# =====================================================

def valid_ipv4(
    address
):

    pattern = (
        r"^(25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)\."
        r"(25[0-5]|"
        r"2[0-4][0-9]|"
        r"[01]?[0-9][0-9]?)$"
    )


    return bool(
        re.match(
            pattern,
            str(address)
        )
    )


# =====================================================
# VALIDATE HOSTNAME
# =====================================================

def valid_hostname(
    hostname
):

    if not hostname:

        return False


    if len(hostname) > 253:

        return False


    pattern = (
        r"^[a-zA-Z0-9]"
        r"([a-zA-Z0-9.-]*"
        r"[a-zA-Z0-9])?$"
    )


    return bool(
        re.match(
            pattern,
            hostname
        )
    )


# =====================================================
# READ RECORDS
# =====================================================

def get_records():

    result = load_zone()


    if not result.get(
        "success",
        False
    ):

        return result


    content = result[
        "content"
    ]


    records = []


    for line in content.splitlines():

        line = line.strip()


        if not line:

            continue


        if line.startswith(
            ";"
        ):

            continue


        parts = line.split()


        if len(parts) < 3:

            continue


        name = parts[0]


        record_type = parts[1]


        if record_type.startswith(
            "$"
        ):

            continue


        if record_type not in (
            ALLOWED_RECORD_TYPES
        ):

            continue


        value = " ".join(
            parts[2:]
        )


        records.append({

            "name":
                name,

            "type":
                record_type,

            "value":
                value

        })


    return {

        "success":
            True,

        "domain":
            PRIMARY_DOMAIN,

        "count":
            len(records),

        "records":
            records

    }


# =====================================================
# DNS STATUS
# =====================================================

def dns_status():

    zone = load_zone()


    if not zone.get(
        "success",
        False
    ):

        return {

            "success":
                False,

            "status":
                "offline",

            "error":
                zone.get(
                    "error",
                    "Unknown error"
                )

        }


    records = get_records()


    return {

        "success":
            True,

        "status":
            "configured",

        "domain":
            PRIMARY_DOMAIN,

        "zone_file":
            str(ZONE_FILE),

        "records":
            records.get(
                "count",
                0
            )

    }


# =====================================================
# SERVER IP REPLACEMENT
# =====================================================

def set_server_ip(
    public_ip
):

    if not valid_ipv4(
        public_ip
    ):

        return {

            "success":
                False,

            "error":
                "Invalid IPv4 address."

        }


    zone = load_zone()


    if not zone.get(
        "success",
        False
    ):

        return zone


    content = zone[
        "content"
    ]


    updated = content.replace(
        "SERVER_PUBLIC_IP",
        public_ip
    )


    try:

        ZONE_FILE.write_text(
            updated,
            encoding="utf-8"
        )


        return {

            "success":
                True,

            "message":
                "Server public IP updated.",

            "ip":
                public_ip

        }


    except Exception as error:

        return {

            "success":
                False,

            "error":
                str(error)

        }


# =====================================================
# DNS CONFIGURATION
# =====================================================

def configuration():

    return {

        "success":
            True,

        "domain":
            PRIMARY_DOMAIN,

        "zone":
            str(ZONE_FILE),

        "nameservers": [

            "ns1.kulzzyradio.com",

            "ns2.kulzzyradio.com"

        ],

        "records": [

            "kulzzyradio.com",

            "www.kulzzyradio.com",

            "control.kulzzyradio.com",

            "api.kulzzyradio.com",

            "code.kulzzyradio.com",

            "radio.kulzzyradio.com",

            "storage.kulzzyradio.com"

        ]

    }


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    print(
        json.dumps(
            dns_status(),
            indent=4
        )
  )
