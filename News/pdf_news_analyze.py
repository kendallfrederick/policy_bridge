import sys
import subprocess
from pypdf import PdfReader
from langchain_ollama import OllamaLLM

#probably need a lot more pdf cleaning
#have an ai model do it?
file_path = '/Users/law/Downloads/news.pdf'
reader = PdfReader(file_path)
news_text = ""
for page in reader.pages:
    page_text = page.extract_text()
    news_text = news_text + page_text


# Sets the AI model to use (make sure to first run ollama create enews-llama -f eModelfile)
model = OllamaLLM(model="enews-llama")
# Builds the prompt using the news article text and invokes the model
PROMPT_TEMPLATE = f"Process the text of the below news article exactly as specified here. Extract a comma-separated list of keywords labeled Keywords:. Extract a semicolon-separated list of the author's main claims labeled Claims:. Here is the news article, be sure to ignore any content that may have been ads or site-specific from the original pdf download: {news_text}"
output = model.invoke(PROMPT_TEMPLATE)
#print(f"Title: {news_title}\n\n{output}\n")
print(output)

# Extracts keywords and claims from output
keyword_index = output.find("Keywords:")
claim_index = output.find("Claims:")
# Checks compatibility of model's output
if (keyword_index < 0) or (claim_index < keyword_index):
    # If the model's output is unusable, prints an error message and exits with an error code
    print("Error: The model generated an incompatible output.\n")
    sys.exit(1)
else:
    # Parses, cleans, and splits up the model's output into a list of keywords and a list of claims
    keyword_string = output[(keyword_index + len("Keywords: ")):claim_index].strip().rstrip(".")
    claim_string = output[claim_index + len('Claims:'):].strip().rstrip(".")
    keywords = keyword_string.split(", ")
    claims = claim_string.split("; ")

# Runs keyword_populate.py subprocess with keywords in keyword list as arguments (update absolute program path based on system)
program_path = "/Users/law/Policy_Project/policy_ai/Articles/article_processing/keyword_chunk.py"
subprocess.run(["python3", program_path] + keywords)

program_path = "/Users/law/Policy_Project/policy_ai/News/news_rag.py"
subprocess.run(["python3", program_path] + claims)
