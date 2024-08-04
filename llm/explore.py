#%%
import os 
import openai 
from dotenv import load_dotenv, find_dotenv
import json

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']


root_dir = '../db/raw/20240802/'
job_emails = read_json(os.path.join(root_dir,'all_jobs.json'))
job_email_samples = job_emails[:100]
# %%
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from langchain.schema.output_parser import StrOutputParser

prompt = ChatPromptTemplate.from_template(
    "tell me a short joke about {topic}"
)

model = ChatOpenAI(model="gpt-4o-mini")
output_parser = StrOutputParser()
chain = prompt | model | output_parser
chain.invoke({"topic": "trash"})


#%% function calling langchain
# tagging function
# Given a function description, select arguments from the input text genreate a structure
# output forming a function call
# more generally - LLM can evaluate the input text and generate a structured output

from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function

class Tagging(BaseModel):
    """Tag the piece of text with particular info."""
    sentiment: str = Field(description="sentiment of text, should be `pos`, `neg`, or `neutral`")
    language: str = Field(description="language of text (should be ISO 639-1 code)")

convert_pydantic_to_openai_function(Tagging)
model = ChatOpenAI(model="gpt-4o-mini",temperature=0.1)
tagging_functions = [convert_pydantic_to_openai_function(Tagging)]

prompt = ChatPromptTemplate.from_messages([
    ("system", "Think carefully, and then tag the text as instructed"),
    ("user", "{input}")
])

model_with_functions = model.bind(
    functions=tagging_functions,
    function_call={"name": "Tagging"}
)

tagging_chain = prompt | model_with_functions
tagging_chain.invoke({"input": "I love langchain"})

#%% extraction
# when given an input json schema, the LLM has been fine tuned to find and 
# fill in the parameters of that schema
# can be used as general purpose extraction.

from typing import Optional
from langchain.output_parsers.openai_functions import JsonOutputFunctionsParser

class Person(BaseModel):
    """Information about a person."""
    name: str = Field(description="person's name")
    age: Optional[int] = Field(description="person's age")


class Information(BaseModel):
    """Information to extract."""
    people: List[Person] = Field(description="List of info about people")

# you can add more functions here
extraction_functions = [convert_pydantic_to_openai_function(Information)]
extraction_model = model.bind(
                functions=extraction_functions,
                function_call={"name": "Information"}
                )

prompt = ChatPromptTemplate.from_messages([
    ("system", "Extract the relevant information, if not explicitly provided do not guess. Extract partial info"),
    ("human", "{input}")
])


extraction_chain = prompt | extraction_model

extraction_chain.invoke(
    "Joe is 30, his mom is Martha. She is 60. Tom is 40 and his daughter is 10."
    )


# add json parser
extraction_chain = prompt | extraction_model | JsonOutputFunctionsParser()
a = extraction_chain.invoke(
    "Joe is 30, his mom is Martha. She is 60. Tom is 40 and his daughter is 10."
    )


#%% extraction using embedding
from langchain_community.document_loaders import UnstructuredURLLoader
urls = ["https://lilianweng.github.io/posts/2023-06-23-agent/"]

loader =  UnstructuredURLLoader(urls=urls)
documents = loader.load()
documents = documents[0]

class Overview(BaseModel):
    """Overview of a section of text."""
    summary: str = Field(description="Provide a concise summary of the content.")
    language: str = Field(description="Provide the language that the content is written in.")
    keywords: str = Field(description="Provide keywords related to the content.")

overview_tagging_function = [
    convert_pydantic_to_openai_function(Overview)
]
tagging_model = model.bind(
    functions=overview_tagging_function,
    function_call={"name":"Overview"}
)
tagging_chain = prompt | tagging_model | JsonOutputFunctionsParser()
tagging_chain.invoke({"input": documents.page_content})

#%%
from langchain.text_splitter import RecursiveCharacterTextSplitter
text_splitter = RecursiveCharacterTextSplitter(chunk_overlap=0)
splits = text_splitter.split_text(documents.page_content)
def flatten(matrix):
    flat_list = []
    for row in matrix:
        flat_list += row
    return flat_list

from langchain.schema.runnable import RunnableLambda

prep = RunnableLambda(
    lambda x: [{"input": doc} for doc in text_splitter.split_text(x)]
)

chain = prep | tagging_chain.map() | flatten


chain.invoke(documents.page_content)

#%%
prompt_template = "respond in json with company name, position, date, location, apply link, description (if available), domain"







[{'name': 'Information',
  'description': 'Information to extract.',
  'parameters': {'$defs': {'Person': {'description': 'Information about a person.',
     'properties': {'name': {'description': "person's name", 'type': 'string'},
      'age': {'anyOf': [{'type': 'integer'}, {'type': 'null'}],
       'description': "person's age"}},
     'required': ['name', 'age'],
     'type': 'object'}},
   'properties': {'people': {'description': 'List of info about people',
     'items': {'description': 'Information about a person.',
      'properties': {'name': {'description': "person's name",
        'type': 'string'},
       'age': {'anyOf': [{'type': 'integer'}, {'type': 'null'}],
        'description': "person's age"}},
      'required': ['name', 'age'],
      'type': 'object'},
     'type': 'array'}},
   'required': ['people'],
   'type': 'object'}}]
# %%
