import json
from gmail_assistant_llm import init_env
import os


def save_json(json_file,data):
    with open(json_file,'w') as f:
        json.dump(data,f)

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def get_path(env_var):
    path = os.path.join(init_env.dotenv_path,env_var)
    return path