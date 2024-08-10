#%%
import os 
from dotenv import load_dotenv
import json
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional
from gmail_assistant_llm import init_env
import json
from gmail_assistant_llm.job_process_pipeline.etl_functions import *

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def get_path(env_var):
    path = os.path.join(init_env.dotenv_path,env_var)
    return path

all_emails = read_json(
    get_path(os.getenv('ALL_EMAILS'))
    )

query_state = read_json(
    get_path(os.getenv('QUERY_GMAIL_STATE'))
    )

job_emails_all = Filter_by_domain(all_emails).filter()
print("Total number of emails processed by LLM is {}".format(len(job_emails_all)))


#%% set up llm
'''
next step:
build LLM to extract:
1. company name
2. position (nested json) - date, location, apply link, description (if available)
3. which domain
'''

class Position(BaseModel):
    '''
    Position information
    '''
    name: str = Field(description='Position Name')
    date: str = Field(description='Date of the job posting')
    location: Optional[str] = Field(description='Location of the job')
    apply_link: str = Field(description='Link to apply for the job')
    description: Optional[str] = Field(description='Description of the job')

class Company(BaseModel):
    '''
    Informaiton about the company
    '''
    name: str = Field(description='Company Name')
    position: Position = Field(description="Position information")


class Parselist(BaseModel):
    '''
    Result of parsing given email
    '''
    query_list: List[Company] = Field(description='list of company information')


extract_function = [
    convert_pydantic_to_openai_function(
    Parselist)
    ]

# replace json key with email id
def add_key(input_json, email_key):
    input_json['email_id'] = email_key
    return input_json

def change_status(input_json):
    input_json['llm_query_status'] = True

# initialze llm
model = ChatOpenAI(model="gpt-4o-mini")
extraction_llm = model.bind(
                functions=extract_function,
                function_call = {'name':"Parselist"},
                           )

prompt = ChatPromptTemplate.from_messages([
    ("system",
        "extract information from json. Your goal is to \
    get informatino about company name and position info. The position \
    information should include post date, location, apply link, \
    description (if available). If you can't find relevant information, \
    please return None"
    ),
    ("human", "{input}")
])

extraction_chain = prompt | extraction_llm

# %% recursively extract information from email
job_process_list = []
llm_meta_list = []


for job_email in job_emails_all:
    email_id = job_email['email_id']
    if query_state[email_id]['llm_query_status']==True:
        print("Email id: {} has already been processed".format(job_email['email_id']))
        continue
    
    print("Processing email id: {}".format(job_email['email_id']))
    print('\n')
    input_data = json.dumps(job_email)

    try:
        chain_result = extraction_chain.invoke({"input": input_data})
        
        json_response = json.loads(
            chain_result.additional_kwargs['function_call']['arguments']
            )

        json_response = add_key(json_response,job_email['email_id'])
        json_response = change_status(json_response)
        
    except Exception as e:
        print("Error processing email id: {}".format(job_email['email_id']))
        print(e)
        # add status to this email
        continue

    # update query state
    query_state[email_id]['llm_query_status'] = True
    job_process_list.append(json_response)
    llm_meta_list.append(chain_result.usage_metadata)


#%% check if job process list had already existed
if os.path.exists(get_path(os.getenv('JOB_LIST'))):
    with open(get_path(os.getenv('JOB_LIST')), 'r') as f:
        job_process_list = json.load(f)

job_list_flat = []

for individual_email in job_process_list:
    for company_info in individual_email['query_list']:
        job_list_flat.append(company_info)


# get job merge data
if os.path.exists(get_path(os.getenv('JOB_LIST_FINAL'))):
    with open(get_path(os.getenv('JOB_LIST_FINAL')), 'r') as f:
        jobs_merge = json.load(f)


existing_companies = [company['name'] for company in jobs_merge]
job_list_overlap = [company for company in job_list_flat if company['name'] in existing_companies]

# merge job list overlap with existing job list
import json
import os
from collections import defaultdict

def merge_json_lists(list1, list2):
    merged = {}
    
    # Process the first list
    for item in list1:
        company_name = item['name']
        merged[company_name] = item
        merged[company_name]['positions'] = item.get('positions', [])

    # Process the second list
    for item in list2:
        company_name = item['name']
        if company_name in merged:
            # If company exists, extend the positions list
            merged[company_name]['positions'].extend(item.get('positions', []))
        else:
            # If company doesn't exist, add it to merged
            merged[company_name] = item
            merged[company_name]['positions'] = item.get('positions', [])

    return list(merged.values())


merged_result = merge_json_lists(jobs_merge, job_process_same)




# company_query_state = {}
# for company in jobs_merge:
#     company_query_state[company['name']] = {}
#     company_query_state[company['name']]['search_state'] = True
#     company_query_state[company['name']]['applied_state'] = False

# # save company query state
# with open(get_path(os.getenv('QUERY_COMPNAY_STATE')),'w') as f:
#     json.dump(company_query_state,f)




#%% save json file
# update query state file
with open(get_path(os.getenv('QUERY_STATE')),'w') as f:
    json.dump(query_state,f)

# update job list files
with open(os.path.join(root_dir,'job_list_all.json'), 'w') as f:
    json.dump(job_process_list, f, indent=2)





# %% calculate avg tokens
# total_input = 0
# total_output = 0
# for meta_data in llm_meta_list:
#     total_input += meta_data['input_tokens']
#     total_output += meta_data['output_tokens']

# avg_input = total_input/len(llm_meta_list)
# avg_output = total_output/len(llm_meta_list)

# input_cost_avg = avg_input * (0.15/1e6)
# output_cost_avg = avg_output * (0.6/1e6)


# %%
