#%%
import openai 
from dotenv import load_dotenv
import json
from langchain_community.utilities import GoogleSearchAPIWrapper
import os
from langchain.prompts import ChatPromptTemplate
from langchain_openai import ChatOpenAI
from pydantic import BaseModel, Field
from langchain.utils.openai_functions import convert_pydantic_to_openai_function
from langchain_core.tools import Tool
import requests
from bs4 import BeautifulSoup

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

dotenv_path = os.path.join('..', '.env')
load_dotenv(dotenv_path)
openai.api_key = os.environ['OPENAI_API_KEY']
root_dir = '../db/20240802'
job_data = read_json(os.path.join(root_dir,'jobs_merge.json'))
# %% filter pending jobs
job_data = [job for job in job_data if job['query_status'] != 'pending']
with open(os.path.join(root_dir,'jobs_merge.json'), 'w') as f:
    json.dump(job_data, f, indent=4)
# %%
industry = []
for job in job_data:
    industry.append(job['industry'])

from collections import Counter
import pandas as pd

# Count the frequencies of each industry
industry_counts = Counter(industry)

# Create a DataFrame from the counts
df = pd.DataFrame.from_dict(industry_counts, orient='index', columns=['count']).reset_index()
df = df.rename(columns={'index': 'industry'})
df = df.sort_values('count', ascending=False)

# Get the top 10 industries
top_10 = df.nlargest(10, 'count')

# Sum the counts of the remaining industries
other_count = df.iloc[10:]['count'].sum()

# Add the "Other" category
other = pd.DataFrame({'industry': ['Other'], 'count': [other_count]})

# Combine top 10 and Other
df_plot = pd.concat([top_10, other])

# Create the bar chart using seaborn
plt.figure(figsize=(12, 6))
sns.barplot(x='industry', y='count', data=df_plot)
plt.title('Distribution of Industries (Top 10 + Other)')
plt.xlabel('Industry')
plt.ylabel('Count')
plt.xticks(rotation=45, ha='right')
plt.tight_layout()

# Display the plot
plt.show()
# %%
