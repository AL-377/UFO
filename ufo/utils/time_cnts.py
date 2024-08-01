import glob
import json
import os
import matplotlib.pyplot as plt

# time consume in different stages
time_cnts = {}
# cnt dimenson
time_cnts["find_control_elements_in_descendants"]=0.0
time_cnts["get_annotation_dict"]=0.0
time_cnts["get_filtered_annotation_dict"]=0.0
time_cnts["capture_app_window_screenshot"]=0.0
time_cnts["capture_app_window_screenshot_with_annotation_dict"]=0.0

time_cnts["get_control_info_list_of_dict"]=0.0
time_cnts["filter get_control_info_list_of_dict"]=0.0


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
    # cnt dimenson
    for key in time_cnts.keys():
        time_cnts[key]=0.0
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
    
    time_cnts["find_control_elements_in_descendants"] += log_json["find_control_elements_in_descendants"]
    time_cnts["get_annotation_dict"] += log_json["get_annotation_dict"]
    time_cnts["get_filtered_annotation_dict"] += log_json["get_filtered_annotation_dict"]
    time_cnts["capture_app_window_screenshot"]+=log_json["capture_app_window_screenshot"]
    time_cnts["capture_app_window_screenshot_with_annotation_dict"]+=log_json["capture_app_window_screenshot_with_annotation_dict"]

    time_cnts["get_control_info_list_of_dict"]+=log_json["get_control_info_list_of_dict"]
    time_cnts["filter get_control_info_list_of_dict"]+=log_json["filter get_control_info_list_of_dict"]
    
    return time_cnts

def get_tasks_time_cnts(tasks_dir:dict):
    global time_cnts  
    init()
    tasks = glob.glob(tasks_dir+"/*")
    for task in tasks:
        if os.path.basename(task)=="0":
            get_task_time_cnts(task)
    for key in time_cnts.keys():
        time_cnts[key] = time_cnts[key]/total_log_cnts
    print(time_cnts)
    print(list(time_cnts.keys()))
    print(list(time_cnts.values()))


def plot(cnts:dict=None,title:str="",keys:list=None,xlabel:str="",ylabel:str=""):
    if cnts:
        if keys:
            values = [cnts[k] for k in keys]
        else:
            keys = list(cnts.keys())
            values = list(cnts.values())
    # Plotting the histogram with values on the bars
    plt.figure(figsize=(30, 3))
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
    get_tasks_time_cnts(r"D:\UFO\logs\2024-07-31-01-06-53")
    plot(cnts=time_cnts,title="LAM-UFO",xlabel="Stage",ylabel="Time Consume(s)",keys=[
        "screen_shot_capture","get_control_info","get_response","execute_response","update_memory","update_status"
    ])
    plot(cnts=time_cnts,title="LAM-UFO-Capture",xlabel="Stage",ylabel="Time Consume(s)",keys=[
        "find_control_elements_in_descendants","get_annotation_dict","get_filtered_annotation_dict","capture_app_window_screenshot","capture_app_window_screenshot_with_annotation_dict"])
    plot(cnts=time_cnts,title="LAM-UFO-Control",xlabel="Stage",ylabel="Time Consume(s)",keys=[
        "get_control_info_list_of_dict","filter get_control_info_list_of_dict"
    ])





