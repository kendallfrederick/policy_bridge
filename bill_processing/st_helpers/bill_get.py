import streamlit as st
from bill_class import Bill
from claimify import get_full_text_df, get_sum_df, get_contents, get_readable, get_readable_sum, get_claims, update_claims, summarize, update_summary
import st_helpers.st_write_helpers as ww
import json
import ndjson
import os 
import streamlit_scrollable_textbox as stx

def summarize_bill(division, title, df, bill):

    section = get_contents(division, title, df)
    full_texts = get_readable(section)

    for i, full_text in enumerate(full_texts):
        if i == 0:
            sum = summarize(full_text)
            print(f"summary after one iteration: {sum}")
        else:
            sum = update_summary(full_text, sum)
            print(f"summary after {i} iterations: {sum}")

def display_congress(congress_num):
    import pandas as pd

    df = pd.read_csv(f'by_congress/{congress_num}_laws_list.csv')
    # st.dataframe(df, hide_index=True, column_config={"Url":None, "Congress":None})

    bigdf = pd.read_csv(f'by_congress/detailed_{congress_num}_laws_list.csv')
    st.dataframe(bigdf, hide_index=True, column_config={"Type":None, "Summary":None, "Url":None, "Congress":None, "Topics":None, "Committees":None, "Related Bills":None, "Text Access":None})

def display_bill(congress_num, num):

    # create the bill
    bill = Bill(int(num), int(congress_num))
    ww.print_st_bill(bill)

    # give user the option to open the original bill in another tab
    url = bill.url
    st.write(f"Open raw bill: {url}")

    if st.button("See related bills", type="secondary"):
        st.subheader("Related Bills")
        list = bill.open_related_bills()
        if len(list) != 0:
            st.write(f"Found {len(list)} related bill.")
        else:
            st.write("None found.")
        for bill in list:
            st.write(f"{bill.type}.{bill.number}: {bill.title}")

    # store the full xml content of the bill
    df = get_full_text_df(bill, num, congress_num)
    
    # print the division outline of the bill. returns number of divisions so 0 if no divisions
    has_divisions = ww.print_divisions(df)

    if has_divisions:
        st.subheader(f"\nWhich division would you like to analyze?")
        division = st.text_input("Enter a letter: ") # get user input on division to analyze
        if division:
            st.write(f"\n\nOkay! Looking at division {division}...\n\n")
            user_entered_div = True
        else:
            user_entered_div = False
    else: 
        division = '' # if the bill doesn't have divisions set that to blank
        user_entered_div = False

    if has_divisions == 0 or user_entered_div:
        # print the title outline of the specific division or whole bill. returns num titles.
        num_titles = ww.print_titles(division, df)

        if num_titles:
            print("\nWhich title would you like to analyze?")
            title = st.text_input("Enter a roman numeral: ") # get user input on division to analyze
            if title: 
                st.write(f"\n\nOkay! Looking at title {title}...\n\n")
                user_entered_title = True
            else: 
                title = ''
                user_entered_title = False
        else: 
            title = ''
            user_entered_title = False

        # if the bill has no titles or the user has entered one
        if num_titles == 0 or user_entered_title:
            sum_df = get_sum_df(bill, num, congress_num)
            if not sum_df.empty:
                # st.write("This is a debug printing step in bill_get.py!!")
                # st.write(sum_df.head())
                filt_sum = get_contents(division, title, sum_df)
                summary = get_readable_sum(filt_sum, division)
                if summary:
                    st.subheader("Summary")
                    if len(summary) > 750:
                        stx.scrollableTextbox(summary, height = 300)
                    else:
                        st.write(summary)
            else: 
                st.warning("This bill doesn't have a summary.")

        return division, title, df, bill

def analyze_bill(division, title, df, bill):
    st.subheader("Section Text Analysis")

    filename = 'saved_jsons.ndjson'
    entries = []

    # Try to load existing NDJSON
    if os.path.exists(filename):
        with open(filename, 'r') as f:
            reader = ndjson.reader(f)
            entries = list(reader)
        print("NDJSON file loaded successfully.")
    else:
        print("Saved NDJSON file doesn't exist yet. Creating it now.")

    name = f"{bill.type}.{bill.number}"

    # Search for existing match
    matched_entry = next(
        (entry for entry in entries if 
         entry['Name'] == name and 
         entry['Title'] == title and 
         entry['Division'] == division),
        None
    )

    if matched_entry:
        st.success(f"Our {bill.subject} expert has already analyzed this! Retrieving their work now.")
        json_obj = matched_entry['JSON']
        parsed_obj = json_obj if isinstance(json_obj, dict) else json.loads(json_obj)
    else:
        # Analyze the section
        section = get_contents(division, title, df)
        full_texts = get_readable(section)

        with st.spinner(f"Consulting our {bill.subject} expert live."):
            json_obj = None
            for i, full_text in enumerate(full_texts):
                if not full_text.strip():
                    continue
                if i == 0:
                    json_obj = get_claims(full_text, bill.subject, bill.summary)
                else:
                    json_obj = update_claims(full_text, json_obj, bill.subject, bill.summary)

        # Ensure we have a string to save and a dict to use
        if isinstance(json_obj, str):
            parsed_obj = json.loads(json_obj)
        elif isinstance(json_obj, dict):
            parsed_obj = json_obj
        else:
            st.warning("Unexpected response format from model.")
            return None, None

        # Save new entry to NDJSON
        new_entry = {
            'Name': name,
            'Title': title,
            'Division': division,
            'JSON': parsed_obj
        }
        entries.append(new_entry)
        with open(filename, 'w') as f:
            ndjson.dump([new_entry], f)

    # Display the JSON content
    if parsed_obj and isinstance(parsed_obj, dict):
        st.subheader("Priorities")
        for purpose in parsed_obj.get("Statement of purpose/priorities", []):
            st.markdown(f"- {purpose}")

        st.subheader("Actions")
        for action in parsed_obj.get("Statements of Action", []):
            st.markdown(f"- {action}")

        st.subheader("Keywords")
        for kw in parsed_obj.get("Keywords", []):
            st.markdown(f"- {kw}")

        st.subheader("Claims")
        for claim in parsed_obj.get("Claims", []):
            st.markdown(f"- {claim}")

        # st.subheader("US CODE AMENDMENT?")
        # for usc in parsed_obj.get("U.S.C.", []):
        #     st.markdown(f"- {usc}")

        return parsed_obj.get("Keywords", []), parsed_obj.get("Claims", [])


def analyze_bill_og(division, title, df, bill):
    import pandas as pd

    st.subheader("Section Text Analysis")

    # check if this section has already been processed
    try:
        json_df = pd.read_csv('saved_jsons.csv')
        print("File loaded successfully.")
    except FileNotFoundError:
        print("Saved json file doesn't exist yet. Making it now.")
        json_df = pd.DataFrame(columns=['Name', 'Title', 'Division', 'JSON'])


    # df stores {bill.type}.{bill.number} (as name) in addition to division and title
    # check if there's an entry in json for the given bill name, division, and title
    name = f"{bill.type}.{bill.number}"

    matched =  json_df[
        (json_df['Name'] == name) & 
        (json_df['Title'] == title) & 
        (json_df['Division'] == division)
    ]

    if not matched.empty: # found match -- this section has already been processed
        json_str = matched.iloc[0,'JSON']
        json_obj = json.loads(json_str)
        st.success(f"Our {bill.subject} expert has already analyzed this! Retrieving their work now.")
    else: # no match, need to run the model to extract claims and then save it
        section = get_contents(division, title, df)
        full_texts = get_readable(section)

        with st.spinner(f"Consulting our {bill.subject} expert live."):
            json_obj = None
            for i, full_text in enumerate(full_texts):
                if i == 0:
                    json_obj = get_claims(full_text, bill.subject)
                else:
                    json_obj = update_claims(full_text, json_obj, bill.subject)
        
        json_str = json.dumps(json_obj, ensure_ascii=False)

        # save the json string to the file
        new_row = {
            'Name': name,
            'Title': title,
            'Division': division,
            'JSON': json_str
        }
        json_df = pd.concat([json_df, pd.DataFrame([new_row])], ignore_index=True)
        json_df.to_csv('saved_jsons.csv', index=False)

    if json_obj and isinstance(json_obj, dict):
        st.write(json_str)
        info = json.loads(json_str)

        purposes = info["Statement of purpose/priorities"]
        st.subheader("Priorities")
        for purpose in purposes:
            st.markdown(f"- {purpose}")

        actions = info["Statements of Action"]
        st.subheader("Actions")
        for action in actions:
            st.markdown(f"- {action}")

        kws = info["Keywords"]
        st.subheader("Keywords")
        for kw in kws:
            st.markdown(f"- {kw}")

        claims = info["Claims"]
        st.subheader("Claims")
        for claim in claims:
            st.markdown(f"- {claim}")

        return kws, claims

    else:
        st.warning("Didn't have anything to analyze")
        return None, None
