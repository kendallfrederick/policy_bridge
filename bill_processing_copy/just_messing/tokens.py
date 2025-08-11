import tiktoken
encoding = tiktoken.encoding_for_model("gpt-3.5-turbo")

from langchain_ollama import OllamaLLM


model = OllamaLLM(model="my-llama") #this is the custom model name made with Modelfile
#make sure to run ollama create my-llama -f Modelfile

PROMPT_TEMPLATE = """
"""


def get_num(file):
    with open(f"output/{file}.txt", "r") as file:
        text = file.read()
        tokens = encoding.encode(text)
        token_count = len(tokens)
        return token_count

def neaten(file):
    with open(f"output/{file}.txt", "r") as file:
        text = file.read()
        PROMPT_TEMPLATE = f'Given this text: {text}, fix the formatting to reduce content to only relevant tokens.'
        output = model.invoke(PROMPT_TEMPLATE)

    print('\n\nResponse\n--------')
    print(output)

num = get_num('water3')
print(f"Total tokens: {num}")

neaten('water3')