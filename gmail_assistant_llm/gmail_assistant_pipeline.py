
from gmail_assistant_llm.job_process_pipeline.general_query import General_Query
from gmail_assistant_llm.job_process_pipeline.llm_query import LLM_Query
from gmail_assistant_llm.job_process_pipeline.llm_search import LLM_Search

# start query
# query_labels = ['inbox','social','promotions','updates']
# query = General_Query(query_labels=query_labels,initialize=False)
# query.run_query()

# start llm query
# add allowed domains 
allowed_domains = ['@linkedin', '@otta', '@untapped', '@indeed','@dice']
llm_query = LLM_Query(allowed_domains=allowed_domains)
llm_query.llm_query()
llm_query.merge_with_history()

# start llm search
llm_search = LLM_Search()
llm_search.run_search()

