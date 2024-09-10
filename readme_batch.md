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