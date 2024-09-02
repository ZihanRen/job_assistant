
from gmail_assistant_llm.job_process_pipeline.gmail_functions import Gmail_Authenticate
authenticate = Gmail_Authenticate()

print("Your gmail credentials PATH is: ", authenticate.PATH_credentials)
print("Your gmail Token PATH is: ", authenticate.PATH_token)
print("Your target query gmail account address: ", authenticate.target_email)



