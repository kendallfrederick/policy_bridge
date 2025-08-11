import streamlit as st
import pandas as pd

import webbrowser

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
                if num_divisions == 0:
                    st.subheader("Divisions")
                st.write(f"{dnum}. {division}")
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
                if num_titles == 0:
                    st.subheader("Titles")
                st.write(f"{tnum}. {title}")
                last_tnum = tnum
                num_titles += 1
        
    return num_titles

def print_st_bill(bill):
    st.header(f"{bill.type}.{bill.number}: {bill.title}")
    st.write(f"A {bill.subject} bill by :blue[{bill.sponsor}]")
    # topics = bill.topics
    # topics_list = ast.literal_eval(topics)
    # for topic in topics_list:
    #     st.markdown("- " + topic)

def open_url_in_browser(url):
    """
    Opens the specified URL in the default web browser.

    Args:
        url (str): The URL to open.
    """
    try:
        webbrowser.open(url)
        print(f"Opened {url} in the default browser.")
    except Exception as e:
        print(f"Error opening URL: {e}")