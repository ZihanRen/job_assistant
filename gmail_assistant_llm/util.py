import json
from gmail_assistant_llm import init_env
import os
import requests
from bs4 import BeautifulSoup

def save_json(json_file,data):
    with open(json_file,'w') as f:
        json.dump(data,f)

def read_json(json_file):
    with open(json_file, 'r') as f:
        data = json.load(f)
    return data

def get_path(env_var):
    path = os.path.join(init_env.dotenv_path,env_var)
    return path

# scrape website to get structured data
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