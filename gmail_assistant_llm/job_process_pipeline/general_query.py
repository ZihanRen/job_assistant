#%%
from gmail_assistant_llm.job_process_pipeline.gmail_functions import Gmail_Authenticate, Gmail_Functions
from gmail_assistant_llm.job_process_pipeline.etl_functions import Merge_New_Emails, Initialize_Emails_List
from gmail_assistant_llm.util import *

class General_Query:
    def __init__(self,initialize = False,query_labels = ['inbox','social','promotions','updates']):
        self.query_labels = query_labels
        self.initialize = initialize

        self.authenticate = Gmail_Authenticate()
        self.gmail_prc = Gmail_Functions(
            target_label_list=query_labels,
            service=self.authenticate.service,
            initialize=initialize
            )

    def run_query(self):
        
        if self.initialize:
            # query all emails and save to list
            email_data = self.gmail_prc.get_all_emails_all_labels()
            self.init_obj = Initialize_Emails_List(email_data)
            self.init_obj.save_emails()
            self.init_obj.init_email_query_state()
        
        else:
            # selectively query emails and merge with existing list
            email_data = self.gmail_prc.get_all_emails_all_labels()
        return email_data
    
    def merge(self,email_data):
        self.merge_etl = Merge_New_Emails(email_data)
        self.merge_etl.merge()


if __name__ == '__main__':

    # read email data
    query = General_Query(initialize=False)
    query.run_query()
