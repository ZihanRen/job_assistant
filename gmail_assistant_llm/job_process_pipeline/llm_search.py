#%%
import json
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
from langchain_core.tools import Tool
from gmail_assistant_llm.job_process_pipeline.etl_functions import *
from gmail_assistant_llm.util import *
from gmail_assistant_llm.job_process_pipeline.llm_templates import Search_Company_LLM

class LLM_Search:
    def __init__(self):
        self.job_data = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
        self.query_company_state = read_json(get_path(os.getenv('QUERY_COMPANY_STATE')))
        self.tagging_chain = Search_Company_LLM().extraction_chain
        self.search = GoogleSearchAPIWrapper()
        self.tool = Tool(
            name="Google Search Snippets",
            description="Search Google for recent results.",
            func=self.top_results,
        )

    def top_results(self, query):
        return self.search.results(query, 1)

    def check_update_query_state(self, company_name):
        if company_name not in self.query_company_state:
            self.query_company_state[company_name] = {
                'search_state': False,
                'applied_state': False
            }

    def run_search(self):
        for i in range(len(self.job_data)):
            # check if this compnay has already been processed
            company_name = self.job_data[i]['name']

            self.check_update_query_state(
                company_name
                )
            
            if self.query_company_state[company_name]['search_state'] == True:
                print(f"Company {company_name} has already been processed. Skipping...")
                print('\n')
                continue


            print(f"Processing {i}th company")
            try:
                top_search = self.tool.run(f"site:linkedin.com What is company {company_name}")
                url = top_search[0]['link']
                structured_data = scrape_website(url)
                input_data = json.dumps(structured_data)
                chain_result = self.tagging_chain.invoke({"input": input_data})
            except Exception as e:
                print(f"Error for company: {company_name} (index: {i})")
                print(f"Error message: {str(e)}")
                print("Skipping this company and continuing...")
                continue


            try:
                json_response = json.loads(
                    chain_result.additional_kwargs['function_call']['arguments']
                    )
            except json.JSONDecodeError as e:
                print(f"JSON Decode Error for company: {company_name} (index: {i})")
                print(f"Error message: {str(e)}")
                print("Skipping this company and continuing...")
                continue
            
            # if successful, update the job_data with the extracted information
            self.job_data[i].update(json_response)
            # update query state
            self.query_company_state[company_name]['search_state'] = True

            # update job merge work with the new data
            save_json(get_path(os.getenv('JOB_LIST_FINAL')),self.job_data)
            save_json(get_path(os.getenv('QUERY_COMPANY_STATE')),self.query_company_state)

    

if __name__ == '__main__':
    search = LLM_Search()
    search.run_search()











# def top_results(query):
#     return search.results(query, 1)

# def check_update_query_state(company_name, query_company_state):
#     if company_name not in query_company_state:
#         query_company_state[company_name] = {
#             'search_state': False,
#             'applied_state': False
#         }
#     return query_company_state

# # openai.api_key = os.environ['OPENAI_API_KEY']
# job_data = read_json(get_path(os.getenv('JOB_LIST_FINAL')))
# query_company_state = read_json(get_path(os.getenv('QUERY_COMPANY_STATE')))
# # initialize llm
# tagging_chain = Search_Company_LLM().extraction_chain
# #initialize search engine
# search = GoogleSearchAPIWrapper()

# tool = Tool(
#     name="Google Search Snippets",
#     description="Search Google for recent results.",
#     func=top_results,
# )




# for i in range(len(job_data)):
#     # check if this compnay has already been processed
#     company_name = job_data[i]['name']

#     query_company_state = check_update_query_state(
#         company_name,
#         query_company_state
#         )
    
#     if query_company_state[company_name]['search_state'] == True:
#         print(f"Company {company_name} has already been processed. Skipping...")
#         print('\n')
#         continue


#     print(f"Processing {i}th company")
#     try:
#         top_search = tool.run(f"site:linkedin.com What is company {company_name}")
#         url = top_search[0]['link']
#         structured_data = scrape_website(url)
#         input_data = json.dumps(structured_data)
#         chain_result = tagging_chain.invoke({"input": input_data})
#     except Exception as e:
#         print(f"Error for company: {company_name} (index: {i})")
#         print(f"Error message: {str(e)}")
#         print("Skipping this company and continuing...")
#         continue


#     try:
#         json_response = json.loads(
#             chain_result.additional_kwargs['function_call']['arguments']
#             )
#     except json.JSONDecodeError as e:
#         print(f"JSON Decode Error for company: {company_name} (index: {i})")
#         print(f"Error message: {str(e)}")
#         print("Skipping this company and continuing...")
#         continue
    
#     # if successful, update the job_data with the extracted information
#     job_data[i].update(json_response)
#     # update query state
#     query_company_state[company_name]['search_state'] = True

#     # update job merge work with the new data
#     save_json(get_path(os.getenv('JOB_LIST_FINAL')),job_data)
#     save_json(get_path(os.getenv('QUERY_COMPANY_STATE')),query_company_state)