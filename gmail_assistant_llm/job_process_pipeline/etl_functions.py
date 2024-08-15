import os
from difflib import SequenceMatcher
from datetime import datetime
from gmail_assistant_llm.util import *
from datetime import datetime

class Initialize_Emails_List:
    def __init__(self, email_data):
        '''
        Initialize email data list
        '''
        self.email_data = email_data
    
    def save_emails(self):

        dir_path = os.path.dirname(get_path(os.getenv('ALL_EMAILS')))

        # Create the directory if it doesn't exist
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        
        # save email data
        save_json(get_path(os.getenv('ALL_EMAILS')),self.email_data)
    
    def init_email_query_state(self):

        # initialize query state
        query_gmail_state = {}
        unique_ids = [email['email_id'] for email in self.email_data]
        unique_ids = list(set(unique_ids))

        for email_id in unique_ids:
            query_gmail_state[email_id] = {}
            query_gmail_state[email_id]['general_query_status'] = True
            query_gmail_state[email_id]['llm_query_status'] = False

        # save query state
        # check folder structure
        dir_path = os.path.dirname(get_path(os.getenv('QUERY_GMAIL_STATE')))
        if not os.path.exists(dir_path):
            os.makedirs(dir_path)
        save_json(get_path(os.getenv('QUERY_GMAIL_STATE')),query_gmail_state)


class Filter_by_domain:

    def __init__(self,
                 all_emails,
                 allowed_domains=['@linkedin', '@otta', '@untapped', '@indeed','@dice']
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

class Merge_New_Emails:
    def __init__(self, new_emails):
        '''
        Merge new emails with all historical emails json object
        update query state from new emails
        '''
        self.new_emails = new_emails
        self.history_emails = read_json(get_path(os.getenv('ALL_EMAILS')))
        self.query_gmail_state = read_json(get_path(os.getenv('QUERY_GMAIL_STATE')))

    def cache(self):
        # get current date in string
        current_date = datetime.now().strftime("%Y%m%d")
        # if folder does not exist, create it
        if not os.path.exists(get_path(os.getenv('CACHE'))):
            os.makedirs(get_path(os.getenv('CACHE')))
        
        save_json(
            os.path.join(get_path(os.getenv('CACHE')),f'history_emails_{current_date}.json'),
            self.history_emails
            )
        save_json(
            os.path.join(get_path(os.getenv('CACHE')),f'query_gmail_state_{current_date}.json'),
            self.query_gmail_state
            )

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



class Merge_New_Job_List:
    def __init__(self, new_jobs):
        '''
        Given two lists:
        new_jobs: new job list
        history_jobs: historical job list
        '''
    
        self.new_jobs = new_jobs
        self.history_jobs = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
        self.existing_companies = [company['name'] for company in self.history_jobs]
        self.job_list_overlap = [company for company in self.new_jobs if company['name'] in self.existing_companies]

    def cache(self):
        # get current date in string
        current_date = datetime.now().strftime("%Y%m%d")
        path = os.path.join(
            get_path(os.getenv('CACHE')),
            f'jobs_list_{current_date}.json'
            )
        
        save_json(path, self.history_jobs)

    def merge_json_lists(self):
        merged = {}
        
        # Helper function to parse date strings
        def parse_date(date_str):
            if date_str is None or date_str == 'None':
                return None
            try:
                return datetime.strptime(date_str, "%Y-%m-%d")
            except ValueError:
                # If parsing fails, return None
                return None
        
        # Process the historical jobs list
        for item in self.history_jobs:
            company_name = item['name']
            merged[company_name] = item
            merged[company_name]['positions'] = item.get('positions', [])
            merged[company_name]['recent_update'] = parse_date(item.get('recent_update'))

        # Process the new jobs list
        for item in self.new_jobs:
            company_name = item['name']
            new_date = parse_date(item.get('recent_update'))
            
            if company_name in merged:
                # If company exists, extend the positions list
                merged[company_name]['positions'].extend(item.get('positions', []))
                # Update date if the new date is more recent and not None
                if new_date is not None and (merged[company_name]['recent_update'] is None or new_date > merged[company_name]['recent_update']):
                    merged[company_name]['recent_update'] = new_date
            else:
                # If company doesn't exist, add it to merged
                merged[company_name] = item
                merged[company_name]['positions'] = item.get('positions', [])
                merged[company_name]['recent_update'] = new_date

        # Convert datetime objects back to string format or 'None'
        for company in merged.values():
            if company['recent_update'] is not None:
                company['recent_update'] = company['recent_update'].strftime("%Y-%m-%d")
            else:
                company['recent_update'] = 'None'

        new_data = list(merged.values())
        return new_data


class Flat_Self_Merge:
    def __init__(self, job_data):
        '''
        Flatten LLM queried job list
        self-merge

        input:
        job_process_list: LLM queried email data
        '''
        
        # job_data: LLM queried email data
        self.job_data = job_data
        self.job_list_flat = []
        

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
            date = item['recent_update']
            
            existing_name = company_exists(company_name)
            
            if existing_name:
                merged[existing_name]['positions'].append(position)
                # Update the date if the current item's date is more recent
                if date > merged[existing_name]['recent_update']:
                    merged[existing_name]['recent_update'] = date
            else:
                merged[company_name] = {
                    'name': company_name, 
                    'positions': [position],
                    'recent_update': date
                }
        
        return list(merged.values())




# merge job list overlap with existing job list
# class Merge_New_Job_List:
#     def __init__(self, new_jobs):

#         '''
#         Given two lists:
#         new_jobs: new job list
#         history_jobs: historical job list
#         '''
    
#         self.new_jobs = new_jobs
#         self.history_jobs = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
#         self.existing_companies = [company['name'] for company in self.history_jobs]
#         self.job_list_overlap = [company for company in self.new_jobs if company['name'] in self.existing_companies]

#     def cache(self):
#         # get current date in string

#         current_date = datetime.now().strftime("%Y%m%d")
#         save_json(f'cache/jobs_list_complete_{current_date}.json',self.history_jobs)

#     def merge_json_lists(self):
#         merged = {}
        
#         # Process the first list
#         for item in self.history_jobs:
#             company_name = item['name']
#             merged[company_name] = item
#             merged[company_name]['positions'] = item.get('positions', [])

#         # Process the second list
#         for item in self.new_jobs:
#             company_name = item['name']
#             if company_name in merged:
#                 # If company exists, extend the positions list
#                 merged[company_name]['positions'].extend(item.get('positions', []))
#             else:
#                 # If company doesn't exist, add it to merged
#                 merged[company_name] = item
#                 merged[company_name]['positions'] = item.get('positions', [])

#         new_data = list(merged.values())
#         return new_data


# class Flat_Self_Merge:
#     def __init__(self, job_data):
#         '''
#         Flatten LLM queried job list
#         self-merge

#         input:
#         job_process_list: LLM queried email data
#         '''
        
#         # job_data: LLM queried email data
#         self.job_data = job_data
#         self.job_list_flat = []
        

#         for individual_email in job_data:
#             for company_info in individual_email['query_list']:
#                 self.job_list_flat.append(company_info)
        
#     def self_merge(self):
#         merged = {}
        
#         def company_exists(name):
#             for existing_name in merged.keys():
#                 if SequenceMatcher(None, name.lower(), existing_name.lower()).ratio() > 0.8:
#                     return existing_name
#             return None

#         for item in self.job_list_flat:
#             company_name = item['name']
#             position = item['position']
            
#             existing_name = company_exists(company_name)
            
#             if existing_name:
#                 merged[existing_name]['positions'].append(position)
#             else:
#                 merged[company_name] = {'name': company_name, 'positions': [position]}
        
#         return list(merged.values())