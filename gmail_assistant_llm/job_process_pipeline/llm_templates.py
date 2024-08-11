from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional


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



class Extraction_LLM:
    def __init__(self):
        self.extract_function = [
            convert_pydantic_to_openai_function(
            Parselist)
            ]

        # initialze llm
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
            )
        
        self.extraction_llm = model.bind(
                        functions=self.extract_function,
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

        self.extraction_chain = prompt | self.extraction_llm

        


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

class Search_Company_LLM:
    def __init__(self):
        self.extract_function = [
            convert_pydantic_to_openai_function(
            Overview)
            ]

        # initialze llm
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
            )
        
        self.extraction_llm = model.bind(
                        functions=self.extract_function,
                        function_call = {'name':"Overview"},
                                )

        prompt = ChatPromptTemplate.from_messages([
            ("system",
                "extract information from web page query results. Your goal is to \
            get informatino about company. If you can't find relevant information, \
            please return None"
            ),
            ("human", "{input}")
        ])

        self.extraction_chain = prompt | self.extraction_llm


# overview_extraction_function = [
#     convert_pydantic_to_openai_function(Overview)
# ]

# model = ChatOpenAI(model="gpt-4o-mini")

# prompt = ChatPromptTemplate.from_messages([
#     ("system",
#         "extract information from web page query results. Your goal is to \
#     get informatino about company. If you can't find relevant information, \
#     please return None"
#     ),
#     ("human", "{input}")
# ])

# tagging_model = model.bind(
#     functions=overview_extraction_function,
#     function_call={"name":"Overview"}
# )

# tagging_chain = prompt | tagging_model