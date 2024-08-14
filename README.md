# Gmail Job Assistant LLM

## Overview

This repository contains a Large Language Model (LLM) assistant powered by GPT-4 mini, designed to help job seekers organize their Gmail accounts, particularly for job alerts from platforms like LinkedIn, Indeed, Untapped, and others. The project uses the Langchain framework and offers a cost-effective solution, processing over 2000 emails for less than $7.

## Features

- Email scraping from Gmail based on specific labels
- ETL process using LLM for structured data extraction
- Company information enrichment via web search
- Continuous updating and merging with historical data
- Export options to Excel or potential for LLM Q&A chatbot integration

## How It Works

1. **Email Scraping**: Retrieves emails from your Gmail account based on specified labels.
2. **ETL Process**: 
   - Extracts structured JSON data from raw email objects
   - LLM assists in parsing position information, company names, dates, etc.
3. **Company Research**: 
   - LLM searches the web for additional company details
   - Gathers info on founding year, IPO status, funding, industry, etc.
4. **Data Integration**: Automatically merges new data with historical database

This process helps job seekers prioritize applications based on their interests and company profiles, saving time on manual research. 😅

## Workflow

[Insert figure here]

## Usage

1. Configure `config.yaml`:
   - Set `initialize` to `False` for continuous updating

2. Run the pipeline:
   ```bash
   cd gmail_assistant_llm
   python gmail_assistant_pipeline.py

## Analysis Options

- Export to Excel (recommended for structured visualization)
- Analyze using pandas
- Develop an agent or LLM Q&A chatbot (for more advanced interactions)

For Excel export, refer to:
`gmail_assistant_llm/post_analytics/analyze_jobs.ipynb`


---

Feel free to contribute or report issues!