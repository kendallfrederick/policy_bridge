import helpers as xx
import pandas as pd
import lxml as etree

import os
import re

from api_client import Client

API_KEY = 'qo7lPHj8lcYm7TK9tEGascFIhm1cWqeZ9PJyxPEh'

def print_lengths(file):

    df = pd.read_csv(f'csv_files/{file}.csv')

    for i in range(len(df)):

        url = df.at[i,'Text Access']
        root = xx.get_xml_from_link(url, API_KEY) 
        body = root.find('legis-body')

        #xx.print_clean_xml(body)
        
        try:
            count = xx.length(body)
            print(f"{df.at[i,'Title']}: {count}")
            #xx.print_clean_xml(body)
        except:
            print(f"{df.at[i,'Title']}: NO BODY")
            continue


# Tags to explicitly preserve as labels in output
PRESERVE_TAGS = {"header", "enum"}

def strip_namespace(tag):
    """Remove XML namespace if present (e.g., {namespace}tag → tag)"""
    return tag.split('}')[-1] if '}' in tag else tag

def extract_with_minimal_tags(element, indent=0):
    """
    Recursively extract readable text from XML,
    preserving only headers and enum numbers (flattening everything else).
    """
    output = []
    tag = element.tag
    prefix = " " * indent

    # Preserve <header> and <enum> tags as labeled lines
    if tag == "header":
        if element.text and element.text.strip():
            output.append(prefix + f"Header: {element.text.strip()}")
    elif tag == "enum":
        if element.text and element.text.strip():
            output.append(prefix + f"{element.text.strip()}")

    # Include inline text from any tag (even non-preserved ones)
    elif element.text and element.text.strip():
        output.append(prefix + element.text.strip())

    # Recursively extract from child elements
    for child in element:
        output.extend(extract_with_minimal_tags(child, indent + 2))

        # Include tail text (text after a closing tag)
        if child.tail and child.tail.strip():
            output.append(" " * indent + child.tail.strip())

    return output

def process_bill(file, output_dir="output"):
    """
    Process a bill from the given URL and write the cleaned output to a text file.

    Parameters:
    - url: XML URL or input source for bill
    - filename: Desired output filename (e.g. "hr1234_cleaned.txt")
    - output_dir: Directory where the file will be saved (default: "output")
    """
    df = pd.read_csv(f'csv_files/{file}.csv')

    for i in range(len(df)):
        url = df.at[i,'Text Access']
        filename = f"{file}{df.at[i,'Number']}"

        root = xx.get_xml_from_link(url, API_KEY)

        # # Strip namespaces from all tags
        # for elem in root.iter():
        #     elem.tag = strip_namespace(elem.tag)

        # Get official title (for display only)
        title = root.find('.//official-title')
        if title is not None and title.text:
            official_title = title.text.strip()
        else:
            official_title = "[No official title found]"

        # Prepare lines for output
        lines = []
        lines.append("=== OFFICIAL TITLE ===")
        lines.append(official_title)
        lines.append("\n=== STRUCTURED BODY ===")

        legis_body = root.find('.//legis-body')
        if legis_body is not None:
            cleaned_lines = extract_with_minimal_tags(legis_body)
            for line in cleaned_lines:
                if line.strip():
                    lines.append(line)
        else:
            lines.append("[No legis-body found]")

        # Ensure output directory exists
        os.makedirs(output_dir, exist_ok=True)

        # Ensure filename ends with .txt
        if not filename.endswith(".txt"):
            filename += ".txt"

        filepath = os.path.join(output_dir, filename)

        # Write cleaned output to file
        with open(filepath, "w", encoding="utf-8") as f:
            for line in lines:
                f.write(line.rstrip() + "\n")

        print(f"Saved output to: {filepath}")



def print_tags(file, number):
    df = pd.read_csv(f'csv_files/{file}.csv')
    url = df.at[number,'Text Access']
    root = xx.get_xml_from_link(url, API_KEY)
    body = root.find('legis-body')

    for element in body.iter():
        if element.tag == 'header':
            print(f"HEADER: {element.text}")
        else:
            string = element.text
            if string:
                print(f"{element.tag}: has {len(string)} characters")
            else:
                print(element.tag)


def list_tags(file):
    df = pd.read_csv(f'csv_files/{file}.csv')
    list = []

    # loop through each bill
    for i in range(len(df)):
        url = df.at[i,'Text Access']

        root = xx.get_xml_from_link(url, API_KEY)
        body = root.find('legis-body')
        if body is not None:
            for element in body.iter():
                if list.count(element.tag) == 0:
                    list.append(element.tag)

    return list
            
def list_all_tags():

    directory = 'csv_files'
    list = []  

    for filename in os.listdir(directory):
        df = pd.read_csv(os.path.join(directory, filename))

        # loop through each bill
        for i in range(len(df)):
            url = df.at[i,'Text Access']

            root = xx.get_xml_from_link(url, API_KEY)
            body = root.find('legis-body')
            if body is not None:
                for element in body.iter():
                    if list.count(element.tag) == 0:
                        list.append(element.tag)

    return list


#print_lengths('econ')
#print_cleaned('water',3)

# list = list_all_tags()

# for item in list:
#     print(item)


#df = pd.read_csv(f'csv_files/water.csv')

#url = df.at[3,'Text Access']

process_bill('health')