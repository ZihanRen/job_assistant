from setuptools import setup, find_packages

setup(
    name="gmail_assistant_llm",
    version="0.1.0",
    packages=find_packages(),
    install_requires=[
        # check requirements.txt
    ],
    author="Zihan Ren",
    author_email="zihanren.ds@gmail.com",
    description="LLM driven job assistant that can query, search and summarize based on Gmail contents",
    long_description=open("README.md").read(),
    long_description_content_type="text/markdown",
    url="https://github.com/ZihanRen/job_assistant",
)