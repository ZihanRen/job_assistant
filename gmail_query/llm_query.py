#%%
import os 
import openai 
from dotenv import load_dotenv, find_dotenv
import json
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser
from langchain_core.output_parsers import JsonOutputParser


def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']


root_dir = '../db/raw/20240802/'
job_emails = read_json(os.path.join(root_dir,'all_jobs.json'))
job_email_samples = job_emails[:10]

#%% set up llm
'''
next step:
build LLM to extract:
1. company name
2. position (nested json) - date, location, apply link, description (if available)
3. which domain
'''

class Position(BaseModel):
    '''
    Position information
    '''
    name: str = Field(description='Position Name')
    date: str = Field(description='Date of the job posting')
    location: Optional[str] = Field(description='Location of the job')
    apply_link: str = Field(description='Link to apply for the job')
    description: Optional[str] = Field(description='Description of the job')

class Company(BaseModel):
    '''
    Informaiton about the company
    '''
    name: str = Field(description='Company Name')
    position: Position = Field(description="Position information")


class Parselist(BaseModel):
    '''
    Result of parsing given email
    '''
    query_list: List[Company] = Field(description='list of company information')


extract_function = [
    convert_pydantic_to_openai_function(
    Parselist)
    ]

# replace json key with email id
def add_key(input_json, email_key):
    input_json['email_id'] = email_key
    return input_json

# initialze llm
model = ChatOpenAI(model="gpt-4o-mini")
extraction_llm = model.bind(
                functions=extract_function,
                function_call = {'name':"Parselist"},
                           )

prompt = ChatPromptTemplate.from_messages([
    ("system",
        "extract information from json. Your goal is to \
    get informatino about company name and position info. The position \
    information should include post date, location, apply link, \
    description (if available). If you can't find relevant information, \
    please return None"
    ),
    ("human", "{input}")
])

extraction_chain = prompt | extraction_llm

# %% recursively extract information from email
job_process_list = []
llm_meta_list = []


for job_email in job_email_samples:
    input_data = json.dumps(job_email)
    chain_result = extraction_chain.invoke({"input": input_data})
    
    json_response = json.loads(
        chain_result.additional_kwargs['function_call']['arguments']
        )

    json_response = add_key(json_response,job_email['email_id'])
    job_process_list.append(json_response)
    llm_meta_list.append(chain_result.usage_metadata)



#%% save json file
with open(os.path.join(root_dir,'job_process_list_sample.json'), 'w') as f:
    json.dump(job_process_list, f, indent=2)





# %% calculate avg tokens
total_input = 0
total_output = 0
for meta_data in llm_meta_list:
    total_input += meta_data['input_tokens']
    total_output += meta_data['output_tokens']

avg_input = total_input/len(llm_meta_list)
avg_output = total_output/len(llm_meta_list)

input_cost_avg = avg_input * (0.15/1e6)
output_cost_avg = avg_output * (0.6/1e6)


# %%
