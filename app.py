import json
import logging

import redis
from celery.result import AsyncResult
from flask import Flask, jsonify, url_for, redirect, send_from_directory
from waitress import serve

from worker import extraction_task

logger = logging.getLogger('waitress')
logger.setLevel(logging.INFO)

api = Flask(__name__)
R = redis.Redis()


@api.route("/api/extract/status/<task_id>", methods=['GET'])
def extract_status(task_id):
    result: AsyncResult = extraction_task.AsyncResult(task_id)

    try:
        if result.state == 'SUCCESS':
            response = {
                'state': result.state,
                'result': json.loads(result.get())
            }
        elif result.state == 'PENDING':
            response = {
                'state': result.state,
            }

        elif result.state == 'FAILURE':
            response = {
                'state': result.state,
            }
        else:
            response = {
                'state': result.state,
            }
    except Exception as e:
        return jsonify({
            "result": "Error",
            "cause": "Task probably didn't exists or already deleted."
        })
    return jsonify(response)


@api.route("/api/extract/<replay_id>", methods=['GET'])
def extract_data(replay_id):
    task: AsyncResult = extraction_task.delay(replay_id)
    return redirect(url_for('extract_status', task_id=task.id))


# JUST A VALIDATION FOR SSL
@api.route("/.well-known/pki-validation/<path:path>", methods=['GET'])
def validation(path):
    return send_from_directory('validation', path)


if __name__ == "__main__":
    serve(api, host='0.0.0.0', port=5000, url_scheme='https')
