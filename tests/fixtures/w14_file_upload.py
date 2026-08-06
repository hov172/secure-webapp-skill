import os

from flask import request

UPLOAD_DIR = "/var/www/html/uploads"


def upload():
    f = request.files["file"]
    dest = os.path.join(UPLOAD_DIR, f.filename)
    f.save(dest)
    return {"url": f"/uploads/{f.filename}"}
