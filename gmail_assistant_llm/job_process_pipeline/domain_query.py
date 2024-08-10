'''
general query: parse raw emails into json
query_job_info: parse each email json object to extract job info
'''
#%%
import os
from gmail_assistant_llm.util import *

all_emails = read_json(
    get_path(os.getenv('ALL_EMAILS'))
    )

previous_jobs = read_json(
    get_path(os.getenv('ALL_EMAILS_JOB'))
    )

query_state = read_json(
    get_path(os.getenv('QUERY_GMAIL_STATE'))
    )


#%%
from gmail_assistant_llm.job_process_pipeline.util import *
job_emails = Filter_by_domain(all_emails).filter()