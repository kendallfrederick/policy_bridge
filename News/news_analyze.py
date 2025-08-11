import sys
import subprocess
from newspaper import Article, ArticleException
from langchain_ollama import OllamaLLM


# Asks the user for the url of a news article they would like to fact check
print("Please provide the full url of the news article you would like to analyze:")
url = input()
#check if input url is for a website that does not allow scraping and return an error if so
#create and store citation with author, title, source, date, url

# Trys to scrape newspaper article off the web and parse it for use
try:
    # Downloads and parses the news article, then extracts key information
    news_article = Article(url, language="en")
    news_article.download()
    news_article.parse()
    news_title = news_article.title
    news_text = news_article.text
except ArticleException as e:
    # If there is any issue accessing or parsing the news article, prints an error message and exits with an error code
    print(f"Error: There was an issue retrieving a news article from the provided url. {e}")
    sys.exit(1)

# Sets the AI model to use (make sure to first run ollama create enews-llama -f eModelfile)
model = OllamaLLM(model="enews-llama")
# Builds the prompt using the news article text and invokes the model
PROMPT_TEMPLATE = f"Process the text of the below news article exactly as specified here. Extract a comma-separated list of keywords labeled Keywords:. Extract a semicolon-separated list of the author's main claims labeled Claims:. Here is the news article: {news_text}"
output = model.invoke(PROMPT_TEMPLATE)
print(f"Title: {news_title}\n\n{output}\n")

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

#Next step is to invoke rag query on newly populated db with prompt formulated to check the validity of the news article's main claims (in a new program?)