from langchain.storage import LocalFileStore
from langchain_community.vectorstores import FAISS
from langchain_community.embeddings import HuggingFaceEmbeddings
from langchain.embeddings import CacheBackedEmbeddings
import os
from datetime import datetime
import shutil
import json
import glob
from concurrent.futures import ThreadPoolExecutor, as_completed

def load_embedding_model(model_name: str):
    store = LocalFileStore("cache/")
    if not model_name.startswith("sentence-transformers"):
        model_name = "sentence-transformers/" + model_name
    embedding_model = HuggingFaceEmbeddings(model_name=model_name)
    cached_embedder = CacheBackedEmbeddings.from_bytes_store(
        embedding_model, store, namespace=model_name
    )
    return cached_embedder

def get_target_file(given_task: str, doc_files_description: dict):
    """
    Get the target file based on the semantic similarity of given task and the template file description.
    """
    candidates = [doc_file_description for doc,
                  doc_file_description in doc_files_description.items()]
    file_doc_descriptions = {doc_file_description: doc for doc,
                             doc_file_description in doc_files_description.items()}
    # use FAISS to get the top k control items texts
    embbeding_model = load_embedding_model("all-MiniLM-L6-v2")
    db = FAISS.from_texts(candidates, embbeding_model)
    doc_descriptions = db.similarity_search(given_task, k=1)
    doc_description = doc_descriptions[0].page_content
    doc = file_doc_descriptions[doc_description]
    return doc

def copy_file(source_file_path, destination_file_path=None):
    """
    Copy a file from one location to another.
    :param source_file_path: The full path to the file you want to copy.
    :param destination_file_path: The full path to the location where you want to copy the file.
    """
    if not destination_file_path:
        # concat the doc file with time info 
        destination_file_path = source_file_path.split(".")[-2] + datetime.datetime.now().strftime('%Y-%m-%d-%H-%M-%S') + "." + source_file_path.split(".")[-1]

    # get the absolute path of destination file
    absolute_path = os.path.abspath(destination_file_path)

    try:
        shutil.copy(source_file_path, destination_file_path)
    except Exception as e:
        print(f"An error occurred: {e}")
        absolute_path = None

    return absolute_path

def process_task(task_file, doc_files_description, doc_template_dir, save_tasks_dir):
    try:
        task = json.load(open(task_file, 'r'))["new_problem"]
        task_no = os.path.basename(task_file).split(".")[0]
        choose_file = get_target_file(task, doc_files_description)
        print(f"Choose: {choose_file}")
        # create a cache file
        object_file = copy_file(
            source_file_path=os.path.join(doc_template_dir, choose_file),
            destination_file_path=os.path.join(save_tasks_dir, "files", f"{task_no}.docx")
        )
        task_json = {"new_problem": task, "action_prefill_file_path": object_file}
        json.dump(task_json, open(os.path.join(save_tasks_dir, "tasks", f"{task_no}.json"), 'w'), indent=4)
    except Exception as e:
        print(str(e))
if __name__ == '__main__':
    # the directory of templates
    doc_template_dir = r".\templates\word"
    doc_files_description = json.load(open(os.path.join(doc_template_dir, "description.json")))
    # the directory to save the samples with original template files
    save_tasks_dir = r".\sample\repair_samples_7"
    os.makedirs(os.path.join(save_tasks_dir, "files"), exist_ok=True)
    os.makedirs(os.path.join(save_tasks_dir, "tasks"), exist_ok=True)
    # the directory of the temp samples(with modified files)
    samples_task_dir = r".\sample\sample_7\sample\task"
    task_files = glob.glob(samples_task_dir + "\*")

    with ThreadPoolExecutor(max_workers=10) as executor:
        futures = [executor.submit(process_task, task_file, doc_files_description, doc_template_dir, save_tasks_dir) for task_file in task_files]
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as exc:
                print(f"An error occurred: {exc}")
