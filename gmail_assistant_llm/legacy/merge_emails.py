from difflib import SequenceMatcher
import os
import openai 
from dotenv import load_dotenv
import json

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']
root_dir = '../db/20240802'
job_data = read_json(os.path.join(root_dir,'job_list_all.json'))

job_list_flat = []

for individual_email in job_data:
    for company_info in individual_email['query_list']:
        job_list_flat.append(company_info)


def merge_companies(data):
    merged = {}
    
    def company_exists(name):
        for existing_name in merged.keys():
            if SequenceMatcher(None, name.lower(), existing_name.lower()).ratio() > 0.8:
                return existing_name
        return None

    for item in data:
        company_name = item['name']
        position = item['position']
        
        existing_name = company_exists(company_name)
        
        if existing_name:
            merged[existing_name]['positions'].append(position)
        else:
            merged[company_name] = {'name': company_name, 'positions': [position]}
    
    return list(merged.values())


jobs_merge = merge_companies(job_list_flat)

# add query status for each company
for company in jobs_merge:
    company['query_status'] = 'pending'

# save json file
with open(os.path.join(root_dir, 'jobs_merge.json'), 'w') as f:
    json.dump(jobs_merge, f)