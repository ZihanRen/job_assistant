#%%
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
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
from langchain_community.document_loaders import UnstructuredURLLoader
import json
from difflib import SequenceMatcher
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
from langchain_community.utilities import GoogleSearchAPIWrapper
from langchain_core.tools import Tool
from langchain_community.document_loaders import UnstructuredURLLoader
import requests
from bs4 import BeautifulSoup
import json

def scrape_website(url):
    # Send a GET request to the URL
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    }
    response = requests.get(url, headers=headers)
    
    # Parse the HTML content
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # Initialize a dictionary to store the scraped data
    data = {
        "url": url,
        "title": soup.title.string if soup.title else "",
        "meta_description": "",
        "headings": [],
        "paragraphs": [],
        "links": []
    }
    
    # Extract meta description
    meta_desc = soup.find("meta", attrs={"name": "description"})
    if meta_desc:
        data["meta_description"] = meta_desc.get("content", "")
    
    # Extract headings
    for heading in soup.find_all(['h1', 'h2', 'h3']):
        data["headings"].append({
            "level": heading.name,
            "text": heading.text.strip()
        })
    
    # Extract paragraphs
    for para in soup.find_all('p'):
        data["paragraphs"].append(para.text.strip())
    
    # Extract links
    for link in soup.find_all('a'):
        data["links"].append({
            "text": link.text.strip(),
            "href": link.get("href", "")
        })
    
    return data

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']
root_dir = '../db/20240802'
job_data = read_json(os.path.join(root_dir,'job_list_all.json'))

# %% merge redundant company into one json
job_list_flat = []

for individual_email in job_data:
    for company_info in individual_email['query_list']:
        job_list_flat.append(company_info)


def merge_companies(data):
    merged = {}
    
    def company_exists(name):
        for existing_name in merged.keys():
            if SequenceMatcher(None, name.lower(), existing_name.lower()).ratio() > 0.8:
                return existing_name
        return None

    for item in data:
        company_name = item['name']
        position = item['position']
        
        existing_name = company_exists(company_name)
        
        if existing_name:
            merged[existing_name]['positions'].append(position)
        else:
            merged[company_name] = {'name': company_name, 'positions': [position]}
    
    return list(merged.values())


jobs_merge = merge_companies(job_list_flat)



#%% initialize llm
class Overview(BaseModel):
    """Overview of a section of text."""
    summary: str = Field(description="Provide a concise summary of the company this url is describing.")
    industry: str = Field(
        description="which industry this company is working for. You should only \
                          choose following: 'tech', 'finance', 'healthcare', 'retail', 'education', 'government', energy \
                          ,'other'. \
                          tech: information, software, hardware, internet, social media, etc. \
                          finance: banking, insurance, investment, etc. \
                          healthcare: hospital, clinic, pharmacy, mental health etc. \
                          retail: store, online shopping, etc. \
                          education: school, university, online course, etc. \
                          government: public service, military, etc. \
                          energy: oil, gas, electricity, etc."
                          )
    size: int = Field(description="Size of this company - number of empolyees")
    founding_year: int = Field(description="Year this company was founded")
    company_url: str = Field(description="URL of the company's website")
    funding: str = Field(description="Funding status of the company - how much do they recieve from investor - which series, \
                         if they are public, simply print out 'ipo'")

overview_extraction_function = [
    convert_pydantic_to_openai_function(Overview)
]

model = ChatOpenAI(model="gpt-4o-mini")

prompt = ChatPromptTemplate.from_messages([
    ("system",
        "extract information from web page query results. Your goal is to \
    get informatino about company. If you can't find relevant information, \
    please return None"
    ),
    ("human", "{input}")
])

tagging_model = model.bind(
    functions=overview_extraction_function,
    function_call={"name":"Overview"}
)

tagging_chain = prompt | tagging_model
 # %% llm search engine to find company information

search = GoogleSearchAPIWrapper()


def top_results(query):
    return search.results(query, 1)


tool = Tool(
    name="Google Search Snippets",
    description="Search Google for recent results.",
    func=top_results,
)

for i in range(len(jobs_merge)):
    print(f"Processing {i}th company")
    print('\n')
    company_name = jobs_merge[i]['name']
    top_search = tool.run(f"site:linkedin.com What is company {company_name}")
    url = top_search[0]['link']
    structured_data = scrape_website(url)
    input_data = json.dumps(structured_data)
    chain_result = tagging_chain.invoke({"input": input_data})

    try:
        json_response = json.loads(
            chain_result.additional_kwargs['function_call']['arguments']
            )
    except json.JSONDecodeError as e:
        print(f"JSON Decode Error for company: {company_name} (index: {i})")
        print(f"Error message: {str(e)}")
        print("Skipping this company and continuing...")
        continue
    
    jobs_merge[i].update(json_response)


# save job merge
with open(os.path.join(root_dir, 'job_complete_profile.json'), 'w') as f:
    json.dump(jobs_merge, f)

