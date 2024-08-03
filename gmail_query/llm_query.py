#%%
import json
import os

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data
