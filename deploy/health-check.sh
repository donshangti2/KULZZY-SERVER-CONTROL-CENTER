#!/bin/bash

API_URL="http://127.0.0.1:5000/"

echo "Checking Kulzzy Server..."

HTTP_STATUS=$(curl \
    -s \
    -o /dev/null \
    -w "%{http_code}" \
    "$API_URL")

if [ "$HTTP_STATUS" = "200" ]; then

    echo "KULZZY SERVER: HEALTHY"

    exit 0

else

    echo "KULZZY SERVER: NOT HEALTHY"

    echo "HTTP STATUS: $HTTP_STATUS"

    exit 1

fi
