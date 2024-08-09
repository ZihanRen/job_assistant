'''
general query: parse raw emails into json
query_job_info: parse each email json object to extract job info
'''
#%%
import json
import os
from dotenv import load_dotenv
import gmail_assistant_llm

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


dotenv_path = os.path.dirname(gmail_assistant_llm.__path__[0])
load_dotenv(dotenv_path)
root_dir = os.path.join(dotenv_path,'db/job/gmail_data/')
all_emails = read_json(root_dir + 'all_emails.json')
previous_jobs = read_json(root_dir + 'all_emails_job.json')


# %%
def filter_job_emails(email_object,allowed_domains):
    
    # Extract the sender email from the metadata
    sender = email_object.get('metadata', {}).get('sender', '')
    
    # Extract the domain part of the email address
    email_parts = sender.split('<')
    if len(email_parts) > 1:
        email_address = email_parts[1].strip('>')
        domain = '@' + email_address.split('@')[-1].lower()
    else:
        # If there's no '<' in the sender field, assume the whole string is the email
        domain = '@' + sender.split('@')[-1].lower()
    
    # Check if the domain is in the allowed list
    return any(allowed_domain in domain for allowed_domain in allowed_domains)

allowed_domains = ['@linkedin', '@otta', '@untapped', '@indeed']
job_emails = [email for email in all_emails if filter_job_emails(email, allowed_domains)]

for email in job_emails:
    email['query_status'] = False


# load previous all emails_job and merge with the new job_emails
all_jobs = read_json(root_dir + 'all_emails_job.json')
job_emails.extend(all_jobs)



#%%
with open(os.path.join(root_dir,'all_emails_job.json'), 'w') as f:
    json.dump(job_emails, f, indent=2)

# %% 

'''
next step:
build LLM to extract:
1. company name
2. position (nested json) - date, location, apply link, description (if available)
3. which domain
4. brief description of this company - search online
5. which industry - do some categorization - search online
6. size - search online
7. whether sponsor h1b - search online
8. startup details - how many rounds - search online
'''

job_samples = job_emails[:40]


# %%
