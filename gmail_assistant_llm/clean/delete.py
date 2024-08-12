#%%
import os
from gmail_assistant_llm.job_process_pipeline.gmail_functions import Gmail_Authenticate
from gmail_assistant_llm.util import *
from googleapiclient.errors import HttpError


authenticate = Gmail_Authenticate()
gmail_query_state = read_json(get_path(os.getenv('QUERY_GMAIL_STATE')))

#%%

def delete_emails(service, email_ids):
    """Delete emails by IDs"""
    for email_id in email_ids:
        try:
            service.users().messages().delete(userId='me', id=email_id).execute()
            print(f"Successfully deleted email with ID: {email_id}")
        except HttpError as error:
            if error.resp.status == 404:
                print(f"Email with ID {email_id} not found. It may have been already deleted.")
            else:
                print(f"An error occurred while deleting email with ID {email_id}: {error}")

delete_ids = [key for key in gmail_query_state.keys() if gmail_query_state[key]['llm_query_status']]
delete_emails(authenticate.service, delete_ids)

