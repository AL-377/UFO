# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from flask import Flask, jsonify,request
import os,json
from ufo.module.client import UFOClientManager
from ufo.module.sessions.session import SessionFactory

app = Flask(__name__)

tasks_dir = "sample/word/tasks/"
logs_dirs = "logs/"

def extract_thoughts(task_log:str)->list:
    """
    Extract thoughts from the response.log file
    :param task_log: The task log name
    :return: list of agent thoughts
    """
    thoughts = []
    with open(os.path.join(logs_dirs,task_log,"response.log"),'r') as file:
        lines = file.readlines()
        for line in lines:
            line_json = json.loads(line.strip())
            if line_json.get("Agent")=="ActAgent":
                thoughts.append(line_json.get("Thought",""))
    return thoughts


@app.route('/hello', methods=['GET'])
def hello():
    return jsonify({'message': 'Hello, the service is up and running!'})


@app.route("/start", methods=["POST"])
def consume():
    global tasks_dir
    data = request.json
    user_name = data.get('user_name')
    task_name = data.get('task_name')
    mode="batch_normal"
    task_log = user_name + "_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    sessions = SessionFactory().create_session(
        task=task_log, mode=mode, plan=tasks_dir + task_name
    )
    clients = UFOClientManager(sessions)
    clients.run_all()
    # extract thoughts from the response.log
    thoughts = extract_thoughts(task_log)
    # return thoughts to the client
    return jsonify({
        "status": "Finish UFO",
        "user_name": user_name,
        "task_name":task_name,
        "thoughts": thoughts
    })

def main():
    app.run(host='localhost', port=6000)

if __name__ == "__main__":
    main()
    