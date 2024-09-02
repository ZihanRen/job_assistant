#%%
import matplotlib.pyplot as plt
import seaborn as sns
from collections import Counter
import pandas as pd
from gmail_assistant_llm.util import *
import os 
import json
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *

job_list = read_json(get_path(os.getenv('JOB_LIST')))
merge_process = Merge_New_Job_List(job_list)
new_job_list = merge_process.merge_json_lists()
save_json(get_path(os.getenv('JOB_LIST_FINAL')),new_job_list)

# %%
