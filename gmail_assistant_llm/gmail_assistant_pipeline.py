#%%
import yaml
from gmail_assistant_llm.job_process_pipeline.general_query import General_Query
from gmail_assistant_llm.job_process_pipeline.llm_query import LLM_Query
from gmail_assistant_llm.job_process_pipeline.llm_search import LLM_Search

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# start query

# query_config = config['general_query']
# query = General_Query(query_labels=query_config['query_labels'], initialize=query_config['initialize'])
# print("Start General Query Process:")
# print(30*'-')
# email_data = query.run_query()
# if not query_config['initialize']:
#     query.merge(email_data)



#%%
# start llm query

# llm_query_config = config['llm_query']
# llm_query = LLM_Query(allowed_domains=llm_query_config['allowed_domains'])
# print("Start LLM Query Process:")
# print(30*'-')
# llm_query.llm_query()

# llm_query.merge_with_history(initialize=llm_query_config['initialize'])


#%%
# start llm search


# print("Start LLM Search Process:")
# print(30*'-')
llm_search = LLM_Search()
llm_search.run_search()


