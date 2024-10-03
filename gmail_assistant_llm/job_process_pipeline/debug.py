#%%
import os 
import json
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *
from gmail_assistant_llm.job_process_pipeline.llm_templates import Extraction_LLM
from gmail_assistant_llm.job_process_pipeline.llm_query import LLM_Query


df_job_current = read_json(get_path(os.getenv('JOB_LIST')))

llm_query = LLM_Query()
llm_query.merge_with_history(initialize=False)

# %%
# get the final job list
job_final = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
# %%
