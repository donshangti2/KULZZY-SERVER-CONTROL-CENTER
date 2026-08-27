import json
from pathlib import Path


# =====================================================
# KULZZY DOMAIN MANAGER
# VERSION 1.0
# =====================================================

BASE_DIR = Path(
    "/srv/kulzzy"
)

CONFIG_FILE = (
    BASE_DIR /
    "config" /
    "domains.json"
)


# =====================================================
# LOAD CONFIGURATION
# =====================================================

def load_domains():

    if not CONFIG_FILE.exists():

        return {

            "success": False,

            "error":
                "Domain configuration file not found."

        }


    try:

        with open(
            CONFIG_FILE,
            "r",
            encoding="utf-8"
        ) as file:

            data = json.load(
                file
            )


        return {

            "success":
                True,

            "domains":
                data

        }


    except Exception as error:

        return {

            "success": False,

            "error":
                str(error)

        }


# =====================================================
# ALL DOMAINS
# =====================================================

def get_all_domains():

    result = load_domains()


    if not result.get(
        "success",
        False
    ):

        return result


    data = result[
        "domains"
    ]


    return {

        "success":
            True,

        "primary_domain":
            data.get(
                "primary_domain",
                ""
            ),

        "domains":
            data.get(
                "domains",
                {}
            )

    }


# =====================================================
# SINGLE DOMAIN
# =====================================================

def get_domain(
    hostname
):

    result = load_domains()


    if not result.get(
        "success",
        False
    ):

        return result


    data = result[
        "domains"
    ]


    domains = data.get(
        "domains",
        {}
    )


    for key, value in domains.items():

        if value.get(
            "hostname"
        ) == hostname:

            return {

                "success":
                    True,

                "name":
                    key,

                "domain":
                    value

            }


    return {

        "success":
            False,

        "error":
            "Domain not found."

    }


# =====================================================
# ENABLED DOMAINS
# =====================================================

def get_enabled_domains():

    result = get_all_domains()


    if not result.get(
        "success",
        False
    ):

        return result


    enabled = []


    for key, domain in result[
        "domains"
    ].items():

        if domain.get(
            "enabled",
            False
        ):

            enabled.append({

                "name":
                    key,

                "hostname":
                    domain.get(
                        "hostname",
                        ""
                    ),

                "service":
                    domain.get(
                        "service",
                        ""
                    )

            })


    return {

        "success":
            True,

        "count":
            len(enabled),

        "domains":
            enabled

    }


# =====================================================
# DOMAIN HEALTH
# =====================================================

def domain_health():

    result = get_enabled_domains()


    if not result.get(
        "success",
        False
    ):

        return result


    return {

        "success":
            True,

        "status":
            "configured",

        "primary_domain":
            get_all_domains().get(
                "primary_domain",
                ""
            ),

        "domain_count":
            result.get(
                "count",
                0
            ),

        "domains":
            result.get(
                "domains",
                []

            )

            }
