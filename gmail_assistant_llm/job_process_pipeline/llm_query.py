#%%
import os 
import json
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *
from gmail_assistant_llm.job_process_pipeline.llm_templates import Extraction_LLM

class LLM_Query:
    def __init__(self,
                 allowed_domains=['@linkedin', '@otta', '@untapped', '@indeed','@dice']
                 ):
        
        
        self.allowed_domains = allowed_domains
        self.all_emails = read_json(
            get_path(os.getenv('ALL_EMAILS'))
            )

        self.query_state = read_json(
            get_path(os.getenv('QUERY_GMAIL_STATE'))
            )

        self.job_emails_all = Filter_by_domain(
            self.all_emails,
            allowed_domains=self.allowed_domains
            ).filter()


        # initialize llm
        self.extraction_llm = Extraction_LLM()
        self.extraction_chain = self.extraction_llm.extraction_chain
    
    @staticmethod
    def add_key(input_json, email_key):
        input_json['email_id'] = email_key
        return input_json
    
    def check_query_state(self,job_email):
        if self.query_state[job_email['email_id']]['llm_query_status']==True:
            print(
                "Email id: {} has already been processed".format(
                    job_email['email_id']
                    )
                )
            return True
        return False

    def update_query_state(self,job_email):
        self.query_state[job_email['email_id']]['llm_query_status'] = True
    
    def cache_query_state(self):
        current_date = datetime.now().strftime("%Y%m%d")
        path = os.path.join(
            get_path(os.getenv('CACHE')),
            f'query_gmail_state_{current_date}.json'
            )
        # check if this cache folder exists
        if not os.path.exists(get_path(os.getenv('CACHE'))):
            os.makedirs(get_path(os.getenv('CACHE')))
        
        save_json(path, self.query_state)
        

    def llm_query(self):
        print('\n')
        print("Starting LLM Query:")
        print('\n')

        # cache the query state
        # add datetime (years, month and day) to cache data name
        self.cache_query_state()

        job_process_list = []

        for job_email in self.job_emails_all:
            if self.check_query_state(job_email):
                continue
            
            print("Processing email id: {}".format(job_email['email_id']))
            print('\n')
            input_data = json.dumps(job_email)

            try:
                json_response = self.extraction_llm.extract_information(input_data)
                if json_response is not None:
                    json_response = self.add_key(json_response,job_email['email_id'])
                else:
                    print("Failed query for email id: {}".format(job_email['email_id']))
                    print('\n')
                    continue

            except Exception as e:
                print("Error processing email id: {}".format(job_email['email_id']))
                print(e)
                continue
            
            # update query state
            self.update_query_state(job_email)
            job_process_list.append(json_response)

        job_flat_list = Flat_Self_Merge(job_process_list).self_merge()
        # update job list
        save_json(get_path(os.getenv('JOB_LIST')),job_flat_list)
        # update query state
        save_json(get_path(os.getenv('QUERY_GMAIL_STATE')),self.query_state)
    
    @staticmethod
    def merge_with_history(initialize=False):
        job_list = read_json(get_path(os.getenv('JOB_LIST')))
        if initialize:
            save_json(get_path(os.getenv('JOB_LIST_FINAL')),job_list)
            # generate query company state
            query_company_state = {}
            for job in job_list:
                query_company_state[job['name']] = {
                    'search_state': False,
                    'applied_state': False
                }
            save_json(get_path(os.getenv('QUERY_COMPANY_STATE')),query_company_state)
        else:
            merge_process = Merge_New_Job_List(job_list)
            new_job_list = merge_process.merge_json_lists()
            # save new list and cache current one
            merge_process.cache()
            save_json(get_path(os.getenv('JOB_LIST_FINAL')),new_job_list)


if __name__ == '__main__':
    # email_id = '19142f79db85c613'
    # job_list = read_json(get_path(os.getenv('JOB_LIST')))
    
    all_emails = read_json(
        get_path(os.getenv('ALL_EMAILS'))
        )
    
    # check emails with specific id
    for email in all_emails:
        if email['email_id'] == '18b26fa7ddfb8377':
            job_email = email
            break
    
    
    input_data = json.dumps(job_email)
    extraction_llm = Extraction_LLM()
    response = extraction_llm.extract_information(input_data)

    # a = LLM_Query.add_key(response,email_id)


    # # print non-query emails
    # llm_query = LLM_Query(
    #     allowed_domains=['@indeed']
    #                       )
    # llm_query.llm_query()
    # LLM_Query.merge_with_history()



# %%
