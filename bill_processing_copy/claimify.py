from langchain_ollama import OllamaLLM
from bill_class import Bill
from lxml import html

import pandas as pd
import roman

from llama_token_counter import LlamaTokenCounter
counter = LlamaTokenCounter()


model = OllamaLLM(model="bill-llama") #this is the custom model name made with Modelfile
# #make sure to run ollama create bill-llama -f Modelfile

# generic model
# model = OllamaLLM(model="llama3.2:latest")

def summarize(text):

    ANSWER_FORMAT = ("""
    { "Summary": ""}"""
    )

    PROMPT_TEMPLATE = (
    
        f"""
        Given the following section of a bill, write a 1-2 sentence summary that captures it's essence.
        You can include purpose, methods, and goals.
           
        Bill section text:
        ###{text}###

        Answer in JSON like this:
        ###{ANSWER_FORMAT}###
        """
    )

    count = counter.count_tokens_sync(PROMPT_TEMPLATE)
    print(f"\n\ngetting summary... the prompt has {count} tokens.\n\n")
    
    output = model.invoke(PROMPT_TEMPLATE)
    return output

def update_summary(s, text):

    ANSWER_FORMAT = ("""
    { "Summary": ""}
    """
    )

    PROMPT_TEMPLATE = (
    
        f"""
        An analyst before you read the earlier part of the bill section, and wrote this summary: {s}.
        Given this next segment, update the summary but keep it under a few sentences.
           
        Next bill segment:
        ###{text}###

        Answer in JSON like this:
        ###{ANSWER_FORMAT}###    
        """
    )

    count = counter.count_tokens_sync(PROMPT_TEMPLATE)
    print(f"\n\ngetting summary... the prompt has {count} tokens.\n\n")
    
    output = model.invoke(PROMPT_TEMPLATE)
    return output

def get_claims(text, subject, summary):

    ANSWER_FORMAT = ("""
    { "Statement of purpose/priorities": [""], "Statements of Action": [""], "Claims": [""], "Keywords": [""]}"""
    )

    PROMPT_TEMPLATE = (
    
        f"""
        You are an experienced policy analyst specialized in {subject}. 
        Given the following section of a bill, extract 
           1. statements of purpose/ policy priorities, 
           2. statements of the actions taken to address those, and 
           3. any statements (claims) you want a scientific expert to fact check.
           4. terms/ keywords from the bill that capture the problem addressed by the bill. This list of keywords will be used to query a database of scientific research.
           5. if the string "U.S.C." is found, extract the section of the US Code that is being amended, for example, "21 U.S.C. 355"
           
        Bill section text:
        ###{text}###

        Also refer to the below section summary to give you more context on the goal and exigence. Statements, terms, and keywords can also come from here.
        ###{summary}###

        Please answer in JSON format like this:
        ###{ANSWER_FORMAT}###
        There should be no text outside the JSON.
        """
    )

    count = counter.count_tokens_sync(PROMPT_TEMPLATE)
    print(f"\n\ngetting claims... the prompt has {count} tokens.\n\n")
    
    output = model.invoke(PROMPT_TEMPLATE)
    return output

def update_claims(text, json,subject, summary):

    ANSWER_FORMAT = ("""
    { "Statement of purpose/priorities": [""], "Statements of Action": [""], "Claims": [""], "Keywords": [""], "U.S.C.": [""]}"""
    )

    PROMPT_TEMPLATE = (
    
        f"""
        You are an experienced policy analyst specialized in {subject}. 
        Given the following section of a bill, extract 
           1. statements of purpose/ policy priorities, 
           2. statements of the actions taken to address those, and 
           3. any statements (claims) you want a scientific expert to fact check.
           4. terms/ keywords from the bill that capture the problem addressed by the bill. This list of keywords will be used to query a database of scientific research.
           5. if the string "U.S.C." is found, extract the section of the US Code that is being amended, for example, "21 U.S.C. 355"
           
        Bill section text:
        ###{text}###

        Also refer to the below section summary to give you more context on the goal and exigence. Statements, terms, and keywords can also come from here.
        ###{summary}###

        The following JSON was created from analyzing the bill text before this section: ({json}) 
        Please update it to retain format like this:
        {ANSWER_FORMAT}
        There should be no text outside the JSON, not even to say "here is the updated json." just start with the bracket.
        """
    )

    count = counter.count_tokens_sync(PROMPT_TEMPLATE)
    print(f"\n\nupdating claims... the prompt has {count} tokens.\n\n")
    output = model.invoke(PROMPT_TEMPLATE)
    return output

def make_bill(number, congress):
    try:
        bill = Bill(number, congress)
        print(f"\n{bill}\n")
        return bill
    except:
        print(f"Error creating Bill object for {congress}-{number}.")
        return None

def get_full_text_df(bill, number, congress):
        
    try: 
        df = bill.content.full_df
        return df
    except:
        print(f"Error accessing full_df for {congress}-{number}.")
        return None
    
def get_sum_df(bill, number, congress):
    
    try: 
        df = bill.content.sum_df
        ####GET RID OF THIS LATER ###### 
        # bill.content.save_to_csv()
        return df
    except:
        print(f"Error accessing full_df for {congress}-{number}.")
        return None
        
def print_divisions(df):
    """
    Print list of all the divisions in the bill.
    """
    last_dnum = None

    num_divisions = 0

    for _, row in df.iterrows():
        division = row['division_header']
        dnum = row['division_number']

        if pd.notna(dnum) and dnum != last_dnum:
            if pd.notna(division) and division != '':
                print(f"Division {dnum}: {division}")
                last_dnum = dnum
                num_divisions += 1

    return num_divisions


def print_titles(division, df):
    """
    Print a list of all the titles in the bill.
    """
    if len(division) > 0:
        filtered = df[df['division_number'] == division]
    else:
        filtered = df

    num_titles = 0

    last_tnum = None
    for _, row in filtered.iterrows():
        title = row['title_header']
        tnum = row['title_number']

        if pd.notna(tnum) and tnum != last_tnum:
            if pd.notna(title) and title != '':
                print(f"Title {tnum}: {title}")
                last_tnum = tnum
                num_titles += 1
        
    return num_titles

def get_contents(division, title, df):
    """
    Return the part of the dataframe that contains the desired
    division and title.
    """
    filt = df # start with full dataframe

    #apply the division filter if specified
    if len(division) > 0:
        filt = filt[filt['division_number'] == division]
    if len(title) > 0:
        filt = filt[filt['title_number'] == title]
    
    return filt

def get_readable(df):
    """
    Return an array of strings with clear division and title labels.
    """

    readable_sections = []
    current_section = ""

    last_division = last_title = last_section = None

    for _, row in df.iterrows():
        division = row['division_header']
        dnum = row['division_number']
        title = row['title_header']
        tnum = row['title_number']
        section = row['section_header']
        snum = row['section_number']
        text = row['text']

        # check if a new section is starting
        if section != last_section:
            if current_section:
                readable_sections.append(current_section)

            current_section = ""

            # Print division header if changed
            if division != last_division:
                current_section += f"\n=== Division {dnum}: {division} ==="
                last_division = division
                last_title = None  # Reset title and section on division change

            # Print title header if changed
            if title != last_title:
                current_section += f"\n--- Title {tnum}: {title} ---"
                last_title = title
                
            # add section header
            current_section += f"\n\n({snum}) {section}: \n\n"
            last_section = section

        # Print the text
        current_section += text
    
    if current_section:
        readable_sections.append(current_section)

    return readable_sections

def get_readable_sum(df, division):
    readable = ""

    last_division = last_title = last_section = None

    for _, row in df.iterrows():
        dnum = row['division_number']
        title = row['title_header']
        tnum = row['title_number']
        text = row['text_chunk']

        # Print division header if changed
        if division != last_division:
            if division:
                readable += f"\n=== Division {dnum} ==="
            last_division = division
            last_title = None  # Reset title and section on division change

        # Print title header if changed
        if title != last_title:
            readable += f"\n--- Title {tnum}: {title} ---"
            last_title = title

        # Print the text
        readable += text

    return readable

def num_to_letter(num):
    if 1 <= num <= 26:
        return chr(ord('A') + num - 1)
    else:
        print("must be 1-26")
        return


def process_all():
    num_divisions = print_divisions(df)

    if num_divisions != 0:
        for i in range(1, num_divisions + 1):
            div_letter = num_to_letter(i)
            print(f"\n{div_letter}\n")
            num_titles = print_titles(div_letter, df)
            print(f"\nNUM TITLES = {num_titles}\n")
            # handle case where division has no titles LATER
            for i in range(1, int(num_titles) + 1):
                print(f"{div_letter} {i}")
                title = roman.toRoman(i)
                section = get_contents(str(div_letter), title, df)
                section.head
                full_texts = get_readable(section)
                for full_text in full_texts:
                    count = counter.count_tokens_sync(full_text)
                    print(f"\n\n\n THIS SECTION HAS {count} TOKENS")

                    if count < 3500: # picked 3800 to give room for system prompt
                        output = get_claims(full_text)
                        print(output)
                    else:
                        print("chunking it now! too long :(")
                        chunks = []
                        while counter.count_tokens_sync(full_text) > 3500:
                            chunks.append(full_text[:10000])
                            rest = full_text[9000:]
                            full_text = rest
                        i = 0
                        json = ""
                        for chunk in chunks:
                            if i == 0:
                                json = get_claims(chunk)
                                i += 1
                            else:
                                json = update_claims(chunk, json)
                                i += 1
                                print(f"{i}: {json}")
                            
                        print(f"\n\nhere's all of the responses! {json}")

    else: 
        division = ''
        num_titles = print_titles(division, df)
        for title_num in range (1, num_titles + 1):
                section = get_contents(div_letter, title_num, df)
                full_texts = get_readable(section)


if __name__ == "__main__":

    number = 3684
    congress = 117

    bill = make_bill(number,congress)

    df = get_full_text_df(bill, number, congress)

    yes_whole_bill = input("Would you like to process the whole bill? ")

    if yes_whole_bill == '1':
        print(f"\nprocessing the whole bill. this will take a minute. \n")
        process_all()
    else:

        has_divisions = print_divisions(df)

        if has_divisions:
            print(f"\nWhich division would you like to analyze?")
            division = input("Enter a letter: ")
            print(f"\n\nOkay! Looking at division {division}...\n\n")
            
        else: 
            division = ''

        print_titles(division, df)

        print("\nWhich title would you like to analyze?")
        title = input("Enter a roman numeral: ")
        print(f"\n\nOkay! Looking at title {title}...\n\n")

        sum_df = get_sum_df(bill, number, congress)
        sum_df.to_csv("testingsumoutput.csv")

        filt_sum = get_contents(division, title, sum_df)
        summary = get_readable_sum(filt_sum, division)
        print(f"Here is the summary: \n {summary}")

        section = get_contents(division, title, df)

        full_texts = get_readable(section)

        print(f"I have retrieved the sections, here are their lengths.\n")

    i = 0
    for full_text in full_texts:
        i += 1
        print(f"{len(full_text)}")

        yes_or_no = input(f"\nWould you like to save the sections to a folder? ")

        if yes_or_no.lower() == 'yes':
            i = 0
            for full_text in full_texts:
                i += 1
                file_path = f"SECTIONS/{number}-{division}{title}-{i}.txt"

                # Write the string to the file in write mode ('w')
                with open(file_path, 'w') as file:
                    file.write(full_text)
                    print(f"SAVED TO {file_path}")
        
        section_number = input(f"What section would you like to analyze? ")
        chosen_section = full_texts[int(section_number) - 1]
        print(chosen_section)

        count = counter.count_tokens_sync(chosen_section)
        print(f"\n\n\n THIS SECTION HAS {count} TOKENS")

        if count < 3500: # picked 3800 to give room for system prompt
            output = get_claims(chosen_section)
            print(output)
        else:
            print("chunking it now! too long :(")
            chunks = []
            while counter.count_tokens_sync(chosen_section) > 3500:
                chunks.append(chosen_section[:10000])
                rest = chosen_section[9000:]
                chosen_section = rest
            i = 0
            json = ""
            for chunk in chunks:
                if i == 0:
                    json = get_claims(chunk)
                    i += 1
                else:
                    json = update_claims(chunk, json)
                    i += 1
                    print(f"{i}: {json}")
                
            print(f"\n\nhere's all of the responses! {json}")



    #next steps#
    '''
    1. loop  through full_texts and if lengths are longer than {figure out appropriate cuttoff}
        chunk them further (ideally in a smart way that keeps sentences together)
    2. enter chain of prompts with llm.
    3. summary should go in first and get a concise description of the purpose of the legislation
        --let the llm pick what would help it the most
    4. pass this brief overview with each chunk segment that goes in so that it can be understood in context.
    5. have the llm categorize each section (amending, budgeting, directing research, etc)
    '''




# PROMPT_TEMPLATE = (
    
#         f"""
#         Given the following list of claims, write a question or several questions that can be asked to a database of scientific research.
#         Each query should be specific and focused on verifying the scientific basis of the claim, and should be formatted as a question.
#         Existing protocols don't matter, focus on aspects of the claim that can be scientifically verified or disproven.
#         As you analyze the claims, also identify any acronyms used and provide their meanings.
        
#         Text:
#         {claims}

#         Answer in the following format:
#         {ANSWER_FORMAT}

#        """
#     )

# print(f"\n\ngetting questions...\n\n")
# output = model.invoke(PROMPT_TEMPLATE)
# print(output)

# results = (
#     f"""{"Questions": [
# "Is there scientific evidence supporting the existence of underground storage facilities or groundwater savings facilities off the Colorado River Indian Tribes reservation?",
# "What is the basis for the claim that the CRIT's allocated water rights are reserved, including the right to use the remaining portion of its allocation?",
# "Can agreements under this act be used to reduce consumptive use of water in a scientifically verifiable manner?",
# "Are there studies or research supporting the benefits of voluntary reduction of water consumption in Lake Mead as a means of conserving water?",
# "Does the United States Environmental Protection Agency (EPA) regulate groundwater storage facilities off the CRIT reservation?",
# "Can agreements under this act be used to protect allottees' water rights from interference, and if so, on what scientific basis?"],
# "Acronyms": {
# "CRIT": "Colorado River Indian Tribes",
# "EPA": "United States Environmental Protection Agency"
# }}""")

