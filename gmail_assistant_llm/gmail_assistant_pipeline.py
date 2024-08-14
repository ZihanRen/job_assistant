import yaml
from gmail_assistant_llm.job_process_pipeline.general_query import General_Query
from gmail_assistant_llm.job_process_pipeline.llm_query import LLM_Query
from gmail_assistant_llm.job_process_pipeline.llm_search import LLM_Search

def load_config(config_path='config.yaml'):
    with open(config_path, 'r') as file:
        return yaml.safe_load(file)

config = load_config()

# start query
query_config = config['general_query']
query = General_Query(query_labels=query_config['query_labels'], initialize=query_config['initialize'])
query.run_query()

# start llm query
llm_query_config = config['llm_query']
llm_query = LLM_Query(allowed_domains=llm_query_config['allowed_domains'])
llm_query.llm_query()
llm_query.merge_with_history(initialize=query_config['initialize'])

# start llm search
llm_search = LLM_Search()
llm_search.run_search()


