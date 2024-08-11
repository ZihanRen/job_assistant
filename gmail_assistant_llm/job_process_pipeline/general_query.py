#%%
from gmail_assistant_llm.job_process_pipeline.gmail_functions import Gmail_Authenticate, Gmail_Functions
from gmail_assistant_llm.job_process_pipeline.etl_functions import Merge_New_Emails
from gmail_assistant_llm.util import *

authenticate = Gmail_Authenticate()
gmail_prc = Gmail_Functions(['job_category'],authenticate.service)
email_data = gmail_prc.get_all_emails_all_labels()

# %% merge with historical data
merge_etl = Merge_New_Emails(email_data)
merge_etl.merge()
history_emails = read_json('cache/history_emails.json')
query_gmail_state = read_json('cache/query_gmail_state.json')






# %%
