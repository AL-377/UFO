# Copyright (c) Microsoft Corporation.
# Licensed under the MIT License.

from datetime import datetime
from flask import Flask, jsonify,request
import os,json
from ufo.module.client import UFOClientManager
from ufo.module.sessions.session import SessionFactory
import win32com.client

app = Flask(__name__)

tasks_dir = "sample/word/tasks/"
logs_dirs = "logs/"

def close_docs():
    """
    Close all opened word documents
    """
    client = win32com.client.Dispatch("Word.Application")
    if client.Documents.Count:
        os.system("taskkill /f /im WINWORD.EXE")

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
    task_file = data.get('task_file')
    mode="batch_normal"
    close_docs()
    task_log = user_name + "_" + datetime.now().strftime("%Y-%m-%d-%H-%M-%S")
    print(f"Start to execute Task {os.path.basename(task_file).split('.')[0]}")
    sessions = SessionFactory().create_session(
        task=task_log, mode=mode, plan=tasks_dir + task_file
    )
    clients = UFOClientManager(sessions)
    res = clients.run_all()
    # extract thoughts from the response.log
    thoughts = extract_thoughts(task_log)
    # return thoughts to the client
    return jsonify({
        "status": "Finish UFO",
        "user_name": user_name,
        "task_file":task_file,
        "thoughts": thoughts
    })
    

def main():
    app.run(host='localhost', port=6000)

if __name__ == "__main__":
    main()
    