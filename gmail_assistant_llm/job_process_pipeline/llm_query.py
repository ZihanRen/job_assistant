#%%
import os 
import json
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *
from gmail_assistant_llm.job_process_pipeline.llm_templates import Extraction_LLM

all_emails = read_json(
    get_path(os.getenv('ALL_EMAILS'))
    )

query_state = read_json(
    get_path(os.getenv('QUERY_GMAIL_STATE'))
    )

job_emails_all = Filter_by_domain(
    all_emails,
    allowed_domains=['@dice']
    ).filter()


print("Total number of emails processed by LLM is {}".format(len(job_emails_all)))

# initialize llm
extraction_chain = Extraction_LLM().extraction_chain


# %% recursively extract information from email
def add_key(input_json, email_key):
    input_json['email_id'] = email_key
    return input_json

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
        
    except Exception as e:
        print("Error processing email id: {}".format(job_email['email_id']))
        print(e)
        continue

    # update query state
    query_state[email_id]['llm_query_status'] = True
    job_process_list.append(json_response)
    llm_meta_list.append(chain_result.usage_metadata)

job_flat_list = Flat_Self_Merge(job_process_list).self_merge()
save_json(get_path(os.getenv('JOB_LIST')),job_flat_list)

#%% merge with history data
job_list_final = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
job_list = read_json(get_path(os.getenv('JOB_LIST')))
merge_process = Merge_New_Job_List(job_list)
new_job_list = merge_process.merge_json_lists()
# save new list and cache current one
merge_process.cache()
save_json(get_path(os.getenv('JOB_LIST_FINAL')),new_job_list)

# %%
