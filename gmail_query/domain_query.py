'''
general query: parse raw emails into json
query_job_info: parse each email json object to extract job info
'''
#%%
import json
import os

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data


root_dir = '../db/raw/20240802/'
category_emails = read_json(root_dir + 'job_category_all.json')
inbox_emails = read_json(root_dir + 'inbox_all.json')
promotion_emails = read_json(root_dir + 'promotions_all.json')
social_emails = read_json(root_dir + 'social_all.json')
all_emails = inbox_emails + promotion_emails + social_emails + category_emails


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


with open(os.path.join(root_dir,'all_jobs.json'), 'w') as f:
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
