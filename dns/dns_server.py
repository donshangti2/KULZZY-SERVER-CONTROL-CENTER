#!/usr/bin/env python3

# =====================================================
# KULZZY DNS SERVER
# VERSION 1.0
# =====================================================

import socket
import struct
import time

from pathlib import Path


# =====================================================
# CONFIGURATION
# =====================================================

HOST = "0.0.0.0"

PORT = 53

DOMAIN = "kulzzyradio.com"


BASE_DIR = Path(
    "/srv/kulzzy"
)


ZONE_FILE = (
    BASE_DIR /
    "dns" /
    "zones" /
    "kulzzyradio.com.zone"
)


# =====================================================
# DNS RECORD STORAGE
# =====================================================

RECORDS = {}


# =====================================================
# LOAD ZONE
# =====================================================

def load_zone():

    global RECORDS

    RECORDS = {}


    if not ZONE_FILE.exists():

        print(
            "DNS zone file not found:"
        )

        print(
            ZONE_FILE
        )

        return


    try:

        content = ZONE_FILE.read_text(
            encoding="utf-8"
        )


        for line in content.splitlines():

            line = line.strip()


            if not line:

                continue


            if line.startswith(";"):

                continue


            parts = line.split()


            if len(parts) < 3:

                continue


            name = parts[0]

            record_type = parts[1]

            value = parts[2]


            if record_type not in (
                "A",
                "AAAA",
                "CNAME",
                "NS"
            ):

                continue


            if name == "@":

                hostname = DOMAIN

            else:

                hostname = (
                    name
                    +
                    "."
                    +
                    DOMAIN
                )


            hostname = hostname.rstrip(
                "."
            ).lower()


            RECORDS.setdefault(
                hostname,
                []
            )


            RECORDS[
                hostname
            ].append({

                "type":
                    record_type,

                "value":
                    value

            })


        print(
            f"Loaded {len(RECORDS)} DNS names."
        )


    except Exception as error:

        print(
            "DNS zone loading error:"
        )

        print(
            error
        )


# =====================================================
# DNS NAME DECODER
# =====================================================

def decode_name(
    data,
    offset
):

    labels = []

    jumped = False

    original_offset = offset


    while True:

        length = data[
            offset
        ]


        if length == 0:

            offset += 1

            break


        if (
            length & 0xC0
        ) == 0xC0:

            pointer = (
                (
                    length
                    &
                    0x3F
                )
                << 8
            ) | data[
                offset + 1
            ]


            if not jumped:

                original_offset = (
                    offset + 2
                )


            offset = pointer

            jumped = True

            continue


        offset += 1


        label = data[
            offset:
            offset + length
        ]


        labels.append(
            label.decode(
                "utf-8",
                errors="ignore"
            )
        )


        offset += length


    name = ".".join(
        labels
    )


    if jumped:

        return (
            name,
            original_offset
        )


    return (
        name,
        offset
    )


# =====================================================
# DNS NAME ENCODER
# =====================================================

def encode_name(
    name
):

    encoded = b""


    for label in name.rstrip(
        "."
    ).split("."):

        encoded += bytes(
            [len(label)]
        )

        encoded += label.encode(
            "utf-8"
        )


    encoded += b"\x00"


    return encoded


# =====================================================
# BUILD A RECORD
# =====================================================

def build_a_record(
    ip
):

    octets = [
        int(x)
        for x in ip.split(".")
    ]


    return struct.pack(
        "!BBBB",
        *octets
    )


# =====================================================
# BUILD ANSWER
# =====================================================

def build_answer(
    name,
    record
):

    record_type = (
        record["type"]
    )


    value = (
        record["value"]
    )


    encoded_name = encode_name(
        name
    )


    ttl = 300


    if record_type == "A":

        rtype = 1

        rclass = 1

        rdata = build_a_record(
            value
        )


    elif record_type == "NS":

        rtype = 2

        rclass = 1

        rdata = encode_name(
            value
        )


    elif record_type == "CNAME":

        rtype = 5

        rclass = 1

        rdata = encode_name(
            value
        )


    elif record_type == "AAAA":

        rtype = 28

        rclass = 1

        rdata = socket.inet_pton(
            socket.AF_INET6,
            value
        )


    else:

        return b""


    return (

        encoded_name

        +

        struct.pack(
            "!HHIH",
            rtype,
            rclass,
            ttl,
            len(rdata)
        )

        +

        rdata

    )


# =====================================================
# DNS QUERY
# =====================================================

def handle_query(
    data
):

    if len(data) < 12:

        return None


    transaction_id = data[
        0:2
    ]


    flags = struct.unpack(
        "!H",
        data[2:4]
    )[0]


    question_count = struct.unpack(
        "!H",
        data[4:6]
    )[0]


    if question_count < 1:

        return None


    query_name, offset = (
        decode_name(
            data,
            12
        )
    )


    if offset + 4 > len(data):

        return None


    qtype, qclass = struct.unpack(
        "!HH",
        data[
            offset:
            offset + 4
        ]
    )


    question_end = (
        offset + 4
    )


    normalized_name = (
        query_name
        .rstrip(".")
        .lower()
    )


    answers = []


    records = RECORDS.get(
        normalized_name,
        []
    )


    for record in records:

        if qtype == 255:

            answers.append(
                record
            )

        elif (
            qtype == 1
            and
            record["type"] == "A"
        ):

            answers.append(
                record
            )

        elif (
            qtype == 2
            and
            record["type"] == "NS"
        ):

            answers.append(
                record
            )

        elif (
            qtype == 5
            and
            record["type"] == "CNAME"
        ):

            answers.append(
                record
            )

        elif (
            qtype == 28
            and
            record["type"] == "AAAA"
        ):

            answers.append(
                record
            )


    response_flags = 0x8000


    # Response
    # Authoritative answer

    response_flags |= 0x0400


    # Recursion available

    response_flags |= 0x0080


    if not answers:

        response_flags |= 0x0003


    header = struct.pack(

        "!HHHHHH",

        struct.unpack(
            "!H",
            transaction_id
        )[0],

        response_flags,

        1,

        len(answers),

        0,

        0

    )


    question = data[
        12:
        question_end
    ]


    answer_data = b""


    for record in answers:

        answer_data += build_answer(
            normalized_name,
            record
        )


    return (
        header
        +
        question
        +
        answer_data
    )


# =====================================================
# UDP SERVER
# =====================================================

def start_server():

    load_zone()


    sock = socket.socket(
        socket.AF_INET,
        socket.SOCK_DGRAM
    )


    sock.setsockopt(
        socket.SOL_SOCKET,
        socket.SO_REUSEADDR,
        1
    )


    sock.bind(
        (
            HOST,
            PORT
        )
    )


    print("")
    print(
        "=========================================="
    )

    print(
        "        KULZZY DNS SERVER"
    )

    print(
        "        VERSION 1.0"
    )

    print(
        "=========================================="
    )

    print(
        f"Listening on {HOST}:{PORT}"
    )

    print(
        f"Domain: {DOMAIN}"
    )

    print(
        "=========================================="
    )


    while True:

        try:

            data, address = (
                sock.recvfrom(
                    4096
                )
            )


            response = handle_query(
                data
            )


            if response:

                sock.sendto(
                    response,
                    address
                )


        except KeyboardInterrupt:

            break


        except Exception as error:

            print(
                "DNS error:",
                error
            )


# =====================================================
# MAIN
# =====================================================

if __name__ == "__main__":

    start_server()
