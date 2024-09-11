### How to run: 

python -m ufo -m batch_query -p path

### Change endpoint: lam and gpt

Config it in the config.yaml. 

### Task format

The task should include 2 dirs: 'files' and 'tasks'.
The task file should include 2 field: 'new_problem' and 'action_prefill_file_path', such as:
{
    "new_problem": "Divide the Microsoft Word page into two columns.",
    "action_prefill_file_path": "C:\\Users\\v-juntinglu\\agents\\process_data\\process_data\\testset/sample_2\\files\\3.docx"
}

### Code env.
Conda activate ufo

### Scene.
1. Data collection:
    1.1 LAM
    1.2 GPT
2. Online Eval

### Analysize
The code in draft.ipynb.
`# evaluate results
offline_evals=[r"logs\2024-08-06-09-16-59-REVIEW46",r"logs\2024-08-06-09-22-19-REVIEW37",r"logs\2024-08-06-09-26-23-REVIEW35"]
raw_log_dir = r"logs\2024-08-06-online-118"
task_res={}
cnt_res={}
step_cnts = {"yes":{},"no":{},"unsure":{}}

for log_dir in offline_evals:
    for eval_dir in glob.glob(log_dir+"/*"):
        try:
            eval_json = json.load(open(os.path.join(eval_dir,"evaluation.log")))
            complete = eval_json.get("complete")
        except:
            continue
        # print(eval_dir)
        # locate the ori log
        response_log = os.path.join(raw_log_dir,os.path.basename(eval_dir),"response.log")
        steps = len(open(response_log,'r').readlines()) - 1
        if steps==0:
            complete="no"
        cnt_res[complete] = cnt_res.get(complete,0) + 1
        task_res[os.path.basename(eval_dir)] = complete
        step_cnts[complete][str(steps)] = step_cnts[complete].get(str(steps),0) + 1
        

print(f"Total tasks: {len(task_res.keys())}")
print(task_res)
print(f"Res Cnts:")
print(cnt_res)
print(f"Success Rate:")
print(cnt_res["yes"] / sum(cnt_res.values()))
print(f"Steps Distribution:")
print(step_cnts)`

### TODO
STMP TQDM.