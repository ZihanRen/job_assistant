#%%
import json
import os
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *
from gmail_assistant_llm.job_process_pipeline.llm_templates import Get_Time_LLM
def parse_json_get_date(job_json):
    position_info = job_json['positions']
    date= []
    for position in position_info:
        if 'date' in position:
            date.append(position['date'])
    return date


job_data = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
# initialize llm
tagging_chain = Get_Time_LLM().extraction_chain


#%%
for i in range(len(job_data)):
    # check if this compnay has already been processed
    time_info = parse_json_get_date(job_data[i])
    company_name = job_data[i]['name']
    print(f"Processing {i}th company")
    input_data = json.dumps(time_info)
    try:    
        chain_result = tagging_chain.invoke({"input": input_data})
    except Exception as e:
        print(f"Error for company: {company_name} (index: {i})")
        print(f"Error message: {str(e)}")
        print("Skipping this company and continuing...")
        continue

    try:
        json_response = json.loads(
            chain_result.additional_kwargs['function_call']['arguments']
            )
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error for company: {company_name} (index: {i})")
        print(f"Error message: {str(e)}")
        print("Skipping this company and continuing...")
        continue
    
    # if successful, update the job_data with the extracted information
    job_data[i].update(json_response)
    # update job merge work with the new data
    save_json(get_path(os.getenv('JOB_LIST_FINAL')),job_data)