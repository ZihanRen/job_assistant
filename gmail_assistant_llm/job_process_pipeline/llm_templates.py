from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from typing import List
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, Field, ValidationError
import json

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
    recent_update: str = Field(description='Date of the email. The format should be in YYYY-MM-DD, like "2024-01-01",\
                                     if dates cannot be found, fill in with None ')


class Parselist(BaseModel):
    '''
    Result of parsing given email
    '''
    query_list: List[Company] = Field(description='list of company information')


class Extraction_LLM:
    def __init__(self):
        self.extract_function = [
            convert_pydantic_to_openai_function(Parselist)
        ]

        # initialize llm
        model = ChatOpenAI(
            model="gpt-4o-mini",
            temperature=0
        )
        
        self.extraction_llm = model.bind(
            functions=self.extract_function,
            function_call={'name': "Parselist"},
        )

        prompt = ChatPromptTemplate.from_messages([
            ("system",
                "You are an AI assistant that extracts information about job postings from provided JSON data. "
                "Your goal is to retrieve information about companies and their job postings. "
                "Each job posting should include the company name, position name, post date, location, apply link, "
                "and description (if available). The 'recent_update' field should be formatted as 'YYYY-MM-DD' (e.g., '2024-01-01'). "
                "If any information is missing or cannot be found, fill it with 'None'. "
                "Only extract information related to job postings. Do not include irrelevant data."
            ),
            ("human", "{input}")
        ])

        self.extraction_chain = prompt | self.extraction_llm

    def parse_date(self, date_str: str) -> Optional[str]:
        for fmt in ('%Y-%m-%d', '%m/%d/%Y', '%d-%b-%Y', '%B %d, %Y'):
            try:
                return datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
            except ValueError:
                continue
        return None


    def parse_llm_output(self, chain_result):
        try:
            # Extract the arguments from the function call
            arguments = chain_result.additional_kwargs['function_call']['arguments']
            
            # Parse the arguments as JSON
            parsed_json = json.loads(arguments)
            
            validated_companies = []
            
            for company in parsed_json['query_list']:
                # Validate company name
                company_name = company.get('name')
                if not company_name:
                    print("Company name missing, skipping this entry.")
                    continue  # Skip this company
                
                # Validate that this is related to a job posting
                position = company.get('position')
                if not position or not position.get('name') or not position.get('apply_link'):
                    print("Incomplete position information, skipping this entry.")
                    continue  # Skip this company

                # Handle 'recent_update'
                recent_update = company.get('recent_update')
                if recent_update:
                    parsed_date = self.parse_date(recent_update)
                    if parsed_date:
                        company['recent_update'] = parsed_date
                    else:
                        company['recent_update'] = datetime.now().strftime('%Y-%m-%d')
                else:
                    company['recent_update'] = datetime.now().strftime('%Y-%m-%d')
                
                validated_companies.append(company)
            
            # Replace the original company list with the validated one
            parsed_json['query_list'] = validated_companies

            return parsed_json
        except (KeyError, json.JSONDecodeError) as e:
            print(f"Error parsing LLM output: {e}")
            return None

    def extract_information(self, input_data):
        try:
            chain_result = self.extraction_chain.invoke({"input": input_data})
            return self.parse_llm_output(chain_result)
        except Exception as e:
            print(f"Error in extract_information for input {input_data}: {e}")
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
    






    # def parse_llm_output(self, chain_result):
    #     try:
    #         # Extract the arguments from the function call
    #         arguments = chain_result.additional_kwargs['function_call']['arguments']
            
    #         # Parse the arguments as JSON
    #         parsed_json = json.loads(arguments)
                        
    #         # Convert string dates to standardized format or None
    #         for company in parsed_json['query_list']:
    #             recent_update = company.get('recent_update', None)

    #         if recent_update:
    #             company['recent_update'] = self.parse_date(recent_update)
    #         else:
    #             company['recent_update'] = None
            
    #         return parsed_json
        
    #     except (KeyError, json.JSONDecodeError) as e:
    #         print(f"Error parsing LLM output: {e}")
    #         return None