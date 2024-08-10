import json
import os
from difflib import SequenceMatcher
from gmail_assistant_llm.util import *

class Merge_New_Emails:
    def __init__(self, new_emails):
        self.new_emails = new_emails
        self.history_emails = read_json(get_path(os.getenv('ALL_EMAILS')))
        self.query_gmail_state = read_json(get_path(os.getenv('QUERY_GMAIL_STATE')))

    def cache(self):
        save_json('cache/history_emails.json',self.history_emails)
        save_json('cache/query_gmail_state.json',self.query_gmail_state)

    def merge(self):
        self.cache()
        for email in self.new_emails:
            email_id = email['email_id']
            if email_id not in self.query_gmail_state:
                self.query_gmail_state[email_id] = {}
                self.query_gmail_state[email_id]['general_query_status'] = True
                self.query_gmail_state[email_id]['llm_query_status'] = False
                # append to the history_emails
                self.history_emails.append(email)

        # update the state and history emails
        save_json(get_path(os.getenv('ALL_EMAILS')),self.history_emails)
        save_json(get_path(os.getenv('QUERY_GMAIL_STATE')),self.query_gmail_state)



class Filter_by_domain:

    def __init__(self,
                 all_emails,
                 allowed_domains=['@linkedin', '@otta', '@untapped', '@indeed']
                 ):
        self.all_emails = all_emails
        self.allowed_domains = allowed_domains
    
    def filter_job_emails(self,email_object):
        
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
        return any(allowed_domain in domain for allowed_domain in self.allowed_domains)
    
    def filter(self):
        job_emails = [email for email in self.all_emails if self.filter_job_emails(email)]
        return job_emails


class Flat_Merge:
    def __init__(self, job_data,history_data=None):
        
        # job_data: LLM queried email data
        self.job_data = job_data
        self.job_list_flat = []
        self.history_data = history_data  

        for individual_email in job_data:
            for company_info in individual_email['query_list']:
                self.job_list_flat.append(company_info)
        
    def self_merge(self):
        merged = {}
        
        def company_exists(name):
            for existing_name in merged.keys():
                if SequenceMatcher(None, name.lower(), existing_name.lower()).ratio() > 0.8:
                    return existing_name
            return None

        for item in self.job_list_flat:
            company_name = item['name']
            position = item['position']
            
            existing_name = company_exists(company_name)
            
            if existing_name:
                merged[existing_name]['positions'].append(position)
            else:
                merged[company_name] = {'name': company_name, 'positions': [position]}
        
        return list(merged.values())