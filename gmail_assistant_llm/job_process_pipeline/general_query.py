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
# query_gmail_state = read_json(get_path(os.getenv('QUERY_GMAIL_STATE')))

# # cached those data first
# save_json('cache/history_emails.json',history_emails)
# save_json('cache/query_gmail_state.json',query_gmail_state)


# for email in email_data:
#     email_id = email['email_id']
#     if email_id not in query_gmail_state:
#         query_gmail_state[email_id] = {}
#         query_gmail_state[email_id]['general_query_status'] = True
#         query_gmail_state[email_id]['llm_query_status'] = False
#         # append to the history_emails
#         history_emails.append(email)

# # update the state and history emails
# save_json(get_path(os.getenv('ALL_EMAILS')),history_emails)
# save_json(get_path(os.getenv('QUERY_GMAIL_STATE')),query_gmail_state)





# %%
