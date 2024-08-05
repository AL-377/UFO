import json
import glob
import os


def fix(task_dir:str):
    tasks = glob.glob(task_dir+"/*")
    for t in tasks:
        t_j = json.load(open(t,'r'))
        t2 = t_j['new_problem'].find("<Previous Actions:> ")
        t_j['new_problem'] = t_j['new_problem'][0:t2].strip()
        json.dump(t_j,open(t,'w'))

def cnt_evaluation_log(log_dir:str,save_file:str):
    """
    Cnt the result from evaluation log
    """
    cnts = {}
    yes_files = []
    unsure_files = [] 
    no_files=[]
    task_dirs = glob.glob(log_dir+"/*")
    for task_dir in task_dirs:
        try:
            eval_json = json.load(open(os.path.join(task_dir,"evaluation.log"),'r'))
            complete_res = eval_json["complete"]
            cnts[complete_res] = cnts.get(complete_res,0) + 1
            if complete_res=='unsure':
                unsure_files.append(task_dir)
            elif complete_res=='yes':
                yes_files.append(task_dir)
            else:
                no_files.append(task_dir)
        except Exception as e:
            continue
    json.dump({
        "cnts":cnts,
        "yes":yes_files,
        "unsure":unsure_files,
        "no":no_files,
        "pass rate":cnts.get("yes",0)/sum(cnts.values())
    },open(save_file,'w'))


if __name__ == '__main__':
    cnt_evaluation_log(r"D:\UFO\logs\2024-08-04-18-37-34","res.json")
    # fix(r"D:\UFO\sample\tasks")
