#%%
import openai 
from dotenv import load_dotenv, find_dotenv
import json
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.output_parsers import JsonOutputParser
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
from langchain_community.document_loaders import UnstructuredURLLoader

import os

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']
root_dir = '../db/20240802'
job_data = read_json(os.path.join(root_dir,'job_process_list_sample.json'))
data = read_json(os.path.join(root_dir,'all_jobs.json'))

# %% merge redundant company into one json
job_list_flat = []

for individual_email in job_data:
    for company_info in individual_email['query_list']:
        job_list_flat.append(company_info)




# %%
import json
from difflib import SequenceMatcher

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
# %% check all companies
companies = []
for job in jobs_merge:
    companies.append(job['name'])

# %%
