import streamlit as st

def main():

    import sys
    import subprocess
    from langchain_ollama import OllamaLLM

    from llama_token_counter import LlamaTokenCounter
    counter = LlamaTokenCounter()
    import pandas as pd

    import st_helpers.article_step as aa
    import st_helpers.claims_step as cc

    import report_class as rr

    import streamlit_scrollable_textbox as stx


    st.title("Congressional Research Reports")

    report_subjects = ['climate','ai']
    subject = st.radio('Select subject', report_subjects)

    path = f"congress_api_to_df/crs/{subject}.csv"
    df = pd.read_csv(path)
    df_simple = df.drop(columns=['update','summary','date'])

    st.dataframe(df_simple)

    id = st.text_input("Enter a report id: ")

    if id:
        report = rr.Report(subject, id)

        st.title(report.title)
        st.write(f"published {report.date}, updated {report.update}")
        st.write(report.pdf)

        st.subheader("Summary")
        stx.scrollableTextbox(report.summary, height = 300)


        reader = rr.remote_pdf_reader(report.pdf)

        news_text = ""
        for page in reader.pages:
            page_text = page.extract_text()
            news_text = news_text + page_text

        # try:
        #     # Open the file in read mode ('r')
        #     with open('test_text.txt', 'r') as file:
        #         # Read the entire content of the file
        #         news_text = file.read()
        
        #     st.write(news_text)

        # except FileNotFoundError:
        #     print("Error: The file 'test_text.txt' was not found.")
        # except Exception as e:
        #     print(f"An error occurred: {e}")

        # Sets the AI model to use (make sure to first run ollama create enews-llama -f eModelfile)
        model = OllamaLLM(model="bill-llama")
        # Builds the prompt using the news article text and invokes the model
        PROMPT_TEMPLATE = (f"""Process the text of the below congressional research report exactly as specified here. 
                        Extract a comma-separated list of keywords labeled Keywords:. 
                        Extract a semicolon-separated list of the author's main claims labeled Claims:. 
                        Here is the CRS report, be sure to ignore footnotes: {news_text}
        """)

        count = counter.count_tokens_sync(PROMPT_TEMPLATE)
        print(f"prompt has {count} tokens")

        st.subheader("Analysis")

        with st.spinner("Extracting claims..."):
            output = model.invoke(PROMPT_TEMPLATE)
        #print(f"Title: {news_title}\n\n{output}\n")
        print(output)
        st.write(output)

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

        with st.spinner("Collecting articles from keywords..."):
            aa.get_articles(keywords)
        with st.spinner("Checking claims against research..."):
            cc.analyze_claims(claims)


if __name__ == "__main__":
    main()