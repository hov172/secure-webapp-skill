import traceback

from flask import Flask, jsonify

app = Flask(__name__)
app.config["DEBUG"] = True


@app.errorhandler(Exception)
def handle_error(exc):
    return jsonify(error=str(exc), trace=traceback.format_exc(), query=getattr(exc, "sql", None)), 500
