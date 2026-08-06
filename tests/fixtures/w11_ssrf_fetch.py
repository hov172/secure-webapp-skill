import requests
from flask import request, jsonify


def preview_link():
    url = request.args["url"]
    resp = requests.get(url, timeout=5)
    return jsonify(status=resp.status_code, body=resp.text[:2000])
