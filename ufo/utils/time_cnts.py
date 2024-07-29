import glob
import json
import os
import matplotlib.pyplot as plt

# time consume in different stages
time_cnts = {}
# cnt dimenson
time_cnts["screen_shot_capture"]=0.0
time_cnts["get_control_info"]=0.0
time_cnts["get_response"]=0.0
time_cnts["execute_response"]=0.0
time_cnts["update_memory"]=0.0
time_cnts["update_status"]=0.0

# log piece cnt
total_log_cnts = 0

def init():
    global time_cnts,total_log_cnts
    time_cnts = {}
    # cnt dimenson
    time_cnts["screen_shot_capture"]=0.0
    time_cnts["get_control_info"]=0.0
    time_cnts["get_response"]=0.0
    time_cnts["execute_response"]=0.0
    time_cnts["update_memory"]=0.0
    time_cnts["update_status"]=0.0
    total_log_cnts = 0


def get_task_time_cnts(task_dir:str): 
    global time_cnts  
    log_files = glob.glob(task_dir+"/*")
    for log_file in log_files:
        if os.path.basename(log_file)=='response.log':
            try:
                log_lines = open(log_file,'r').readlines()
                if len(log_lines)==0:
                    break
                for log_line in log_lines:
                    log_json = json.loads(log_line)
                    if "agent_name" in log_json and log_json["agent_name"]=="AppAgentProcessor":
                        get_piece_time_cnts(log_json)
            except:
                break
    
        
def get_piece_time_cnts(log_json:dict):
    global total_log_cnts,time_cnts
    total_log_cnts += 1
    time_cnts["screen_shot_capture"] = time_cnts["screen_shot_capture"] + log_json["Capture screenshot"]
    time_cnts["get_control_info"] = time_cnts["get_control_info"] + log_json["Get control information"]
    time_cnts["get_response"] = time_cnts["get_response"] + log_json["Get response"]
    time_cnts["execute_response"] = time_cnts["execute_response"] + log_json["Execute action"]
    time_cnts["update_memory"] = time_cnts["update_memory"] + log_json["Update memory"]
    time_cnts["update_status"] = time_cnts["update_status"] + log_json["Update status"]
    return time_cnts

def get_tasks_time_cnts(tasks_dir:dict):
    global time_cnts  
    tasks = glob.glob(tasks_dir+"/*")
    for task in tasks:
        if os.path.basename(task)=="0":
            get_task_time_cnts(task)
    for key in time_cnts.keys():
        time_cnts[key] = time_cnts[key]/total_log_cnts
    print(time_cnts)
    print(list(time_cnts.keys()))
    print(list(time_cnts.values()))
    return time_cnts


def plot(cnts:dict=None,title:str="",keys:list=None,values:list=None,xlabel:str="",ylabel:str=""):
    if not keys or values:
        keys = list(cnts.keys())
        values = list(cnts.values())
    # Sort the keys and values based on the keys
    keys, values = zip(*sorted(zip(keys, values)))
    # Plotting the histogram with values on the bars
    plt.figure(figsize=(20, 6))
    bars = plt.bar(keys, values, color='skyblue', edgecolor='black')

    # Adding value labels on top of each bar
    for bar in bars:
        height = bar.get_height()
        plt.text(bar.get_x() + bar.get_width() / 2.0, height, str(height), ha='center', va='bottom')

    plt.xlabel(xlabel)
    plt.ylabel(ylabel)
    plt.title(title)
    plt.xticks(keys)  # Ensure all keys are shown on the x-axis
    plt.grid(axis='y')

    # Show the plot
    plt.show()


if __name__ == "__main__":
    init()
    time_cnts = get_tasks_time_cnts(r"D:\UFO\logs\2024-07-29-04-43-11")
    plot(time_cnts,title="LAM-UFO",xlabel="Stage",ylabel="Time Consume(s)")
    init()
    time_cnts = get_tasks_time_cnts(r"D:\UFO_GPT\UFO\logs\2024-07-26-08-53-39")
    plot(time_cnts,title="GPT-UFO",xlabel="Stage",ylabel="Time Consume(s)")





