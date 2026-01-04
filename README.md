# **PolicyBridge**
_Bridging the gap between policy and science using Retrieval Augmented Generation_

We have developed and AI agent to fact-check congressional research reports and bills against scientific research. Using Langchain for AI integration, we bridge the CORE API to the Congress.gov API and ultimately produce claim analysis for bills and reports grounded in scientific research.

# Requirements 

* Ollama
* llama3.2
* docker
* weaviate
* langchain
* streamlit

See detailed requirements.txt file in bill_processing folder. Note that once Ollama is installed, you will need to run 
`Ollama create my-llama -f Modelfile`
 
# Usage

`Streamlit run Home.py`
in bill_processing. 

# Contact Information

Kendall Frederick | 2025 SWE Summer Intern at Intelligenesis LLC |
Johns Hopkins University '28 |
kfrede14@jh.edu

Aleah Dinmore |
2025 SWE Summer Intern at Intelligenesis LLC |
Stevens Institute of Technology '27 |  
adinmore@stevens.edu
