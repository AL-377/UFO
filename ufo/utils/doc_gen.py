import json
import os
from typing import List, Tuple

class DocGenerator:
    def __init__(self, doc_type: str):
        self.doc_type = doc_type

    def _load_logs(self,png_prefix:str,eval_file:str,request_file:str,resp_file:str,log_dir:str):
        imgs = []
        for file in os.listdir(log_dir):
            # get the time of the file generatio
            if file.endswith('.png') and file.startswith(png_prefix):
                    imgs.append((file))
        # sort the imgs by time

        
    def generate(self,save_path:str, data: List[Tuple[str, str]]):
        for name, content in data:
            with open(os.path.join(save_path, f'{name}.json'), 'w') as f:
                json.dump(content, f)