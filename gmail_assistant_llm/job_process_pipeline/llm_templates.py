from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional
from datetime import datetime



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
    date: datetime = Field(description='Date of the email. The format should be in YYYY-MM-DD, like "2024-01-01" ')


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
    
    def parse_date(self, date_str: str) -> Optional[datetime]:
        try:
            return datetime.strptime(date_str, '%Y-%m-%d')
        except ValueError:
            return None

        


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



class Time_Extractor(BaseModel):
    """Extracts the most recent date from a list of date strings."""
    recent_update: str = Field(description="The most recent date found in the list, in the format YYYY-MM-DD. \
                               If no valid date is found, return None.")

class Get_Time_LLM:
    def __init__(self):
        self.extract_function = [
            convert_pydantic_to_openai_function(Time_Extractor)
        ]

        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        
        self.extraction_llm = model.bind(
            functions=self.extract_function,
            function_call={'name': "Time_Extractor"},
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system",
             "You are an expert in date extraction and interpretation. Your task is to analyze a list of strings that may contain date information. "
             "These strings can include various date formats, both standard (like YYYY-MM-DD) and non-standard (like 'last Tuesday'), as well as semantic references (like 'updated yesterday'). "
             "Your goal is to:"
             "1. Identify all potential dates in the list."
             "2. Interpret any semantic date references relative to the current date."
             "3. Convert all identified dates to a standard YYYY-MM-DD format."
             "4. Determine the most recent date among all identified dates."
             "5. Return the most recent date in YYYY-MM-DD format."
             "If you can't find any valid dates or if the date references are too ambiguous, return None."
             "Remember, accuracy is crucial. If you're unsure about a date reference, it's better to exclude it than to make an incorrect assumption."),
            ("human", "{input}")
        ])

        self.extraction_chain = prompt | self.extraction_llm