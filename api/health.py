from flask import jsonify


def health_response():

    return jsonify({

        "service": "Kulzzy Server",

        "status": "healthy",

        "server": "kulzzy-server-01",

        "version": "1.0.0"

    })
