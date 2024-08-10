import gmail_assistant_llm
from dotenv import load_dotenv
import os

dotenv_path = os.path.dirname(gmail_assistant_llm.__path__[0])
load_dotenv(os.path.join(dotenv_path,'.env'))
