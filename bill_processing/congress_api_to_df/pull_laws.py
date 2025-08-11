import xml.etree.ElementTree as ET
from api_client import Client
import requests
import webbrowser

import helpers as xx

import pandas as pd

def get_subjects_list(client, number, type, congress):
    """
    Returns a tuple. 
    First element is in bytes utf-8 encoded. 
    Second element is integer number of laws
    """
    endpoint = f"bill/{congress}/{type}/{number}/subjects"
    law_list = client.get(endpoint)

    bytes = law_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    subjects = []

    for item in root.findall('./subjects/legislativeSubjects/item'):
        name = item.find('name')
        if name is not None:
            name_text = name.text.strip()
            subjects.append(name_text)
    
    return subjects

def get_committees_list(client, number, type, congress):
    """
    Returns a tuple. 
    First element is in bytes utf-8 encoded. 
    Second element is integer number of laws
    """
    endpoint = f"bill/{congress}/{type}/{number}/committees"
    law_list = client.get(endpoint)

    bytes = law_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    committees = []

    for item in root.findall('./committees/item'):
        name = item.find('name')
        if name is not None:
            name_text = name.text.strip()
            committees.append(name_text)

        subcommittees = item.findall('subcommittees/item/name')
        for sub in subcommittees:
            sub_name = sub.text.strip()
            committees.append(sub_name)

    return committees

def get_related_list(client, number, type, congress):
    """
    Returns a tuple. 
    First element is in bytes utf-8 encoded. 
    Second element is integer number of laws
    """
    endpoint = f"bill/{congress}/{type}/{number}/relatedbills"
    law_list = client.get(endpoint)

    bytes = law_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    urls = []

    for item in root.findall('./relatedBills/item'):
        url = item.find('url')
        if url is not None:
            url_text = url.text.strip()
            urls.append(url_text)
    
    return urls

def get_summary(client, number, type, congress):
    """
    Returns a tuple. 
    First element is in bytes utf-8 encoded. 
    Second element is integer number of laws
    """
    endpoint = f"bill/{congress}/{type}/{number}/summaries"
    law_list = client.get(endpoint)

    bytes = law_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    #print_clean_xml(root)

    for item in root.findall('./summaries/summary'):
        action_desc = item.findtext('actionDesc')
        if action_desc and action_desc.strip() == "Public Law": # change to "Introduced in Senate" for 119th congress
            cdata_node = item.find('cdata')
            if cdata_node is not None:
                text_node = cdata_node.find('text')
                if text_node is not None:
                    summary_parts = []
                    for elem in text_node.iter():
                        if elem.text:
                            summary_parts.append(elem.text.strip())
                    summary_text = ' '.join(summary_parts)
                    return summary_text
    return 'No summary available'

def get_laws_list(client, congress, total_needed=300):
    """
    Returns a DataFrame with all laws up to total_needed.
    """
    all_data = []
    offset = 0
    limit = 250

    while len(all_data) < total_needed:
        endpoint = f"law/{congress}?limit={limit}&offset={offset}"
        law_list = client.get(endpoint)

        bytes = law_list[0]
        string = bytes.decode('utf-8')
        root = ET.fromstring(string)

        numbers = [bill.text.strip() for bill in root.findall('./bills/bill/number')]
        types = [bill.text.strip() for bill in root.findall('./bills/bill/type')]
        congresses = [bill.text.strip() for bill in root.findall('./bills/bill/congress')]
        titles = [bill.text.strip() for bill in root.findall('./bills/bill/title')]
        urls = [bill.text.strip() for bill in root.findall('./bills/bill/url')]

        # Transpose and append
        batch_data = list(zip(numbers, types, congresses, titles, urls))
        all_data.extend(batch_data)

        if len(batch_data) < limit:
            break  # No more data to fetch

        offset += limit

    # Truncate to total_needed if necessary
    all_data = all_data[:total_needed]
    df = pd.DataFrame(all_data, columns=['Number', 'Type', 'Congress', 'Title', 'Url'])
    return df

def get_laws_list_orig(client, congress, mode):
    """
    Returns a tuple. 
    First element is in bytes utf-8 encoded. 
    Second element is integer number of laws
    """

    if mode == 'a':
        offset = 250 # change this to the last offset processed in the existing file
    if mode == 'w':
        offset = 0

    endpoint = f"law/{congress}?limit=250&offset={offset}" # change offset to 0 for first 250
    law_list = client.get(endpoint)

    bytes = law_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    #use the xml to make lists of all important info
    numbers = []
    for bill in root.findall('./bills/bill/number'):
        numbers.append(bill.text.strip())

    types = []
    for bill in root.findall('./bills/bill/type'):
        types.append(bill.text.strip())

    congress = []
    for bill in root.findall('./bills/bill/congress'):
        congress.append(bill.text.strip())

    titles = []
    for bill in root.findall('./bills/bill/title'):
        titles.append(bill.text.strip())

    urls = []
    for bill in root.findall('./bills/bill/url'):
        urls.append(bill.text.strip())

    #create a list of lists
    data = [numbers, types, congress, titles, urls]
    df = pd.DataFrame(data)
    return df

def print_clean_xml(elem, level=0):
    indent = '  ' * level
    print(f"{indent}<{elem.tag}>")
    
    # Print text if present and not just whitespace
    if elem.text and elem.text.strip():
        print(f"{indent}  {elem.text.strip()}")

    # Recurse on children
    for child in elem:
        print_clean_xml(child, level + 1)

    print(f"{indent}</{elem.tag}>")

def detailed_laws_list(client, congress):

    df = pd.read_csv(f"by_congress/{congress}_laws_list.csv")

    nums = df['Number']
    types = df['Type']
    congresses = df['Congress']
    urls = df['Url']

    df['Summary'] = None
    df['Committees'] = None
    df['Topics'] = None
    df['Related Bills'] = None
    df['Sponsor'] = None
    df['Subject'] = None
    df['Text Access'] = None

    def edit_df():
        print(i)
        number = int(nums[i])
        type = types[i].lower()
        congress = int(congresses[i])
        url = urls[i]
        try: 
            root = xx.get_xml_from_link(url, API_KEY)
        except Exception as e:
            print(f"Error fetching XML for record {i}: {e}")
            return

        # get summary
        try:
            df.at[i, 'Summary'] = get_summary(client, number, f'{type}', congress)
        except Exception as e:
            print(f"Error fetching summary for record {i}: {e}")
            df.at[i, 'Summary'] = None
        
        # get committees
        try:
            df.at[i, 'Committees'] = get_committees_list(client, number, f'{type}', congress)
        except Exception as e:
            print(f"Error fetching committees for record {i}: {e}")
            df.at[i, 'Committees'] = None

        # get subjects
        try:
            df.at[i, 'Topics'] = get_subjects_list(client, number, f'{type}', congress)
        except Exception as e:
            print(f"Error fetching subjects for record {i}: {e}")
            df.at[i, 'Topics'] = None

        # get related bills
        try:
            related = get_related_list(client, number, f'{type}', congress)
            df.at[i, 'Related Bills'] = ', '.join(related) if related else None
        except Exception as e:
            print(f"Failed to get related bills for bill {number}: {e}")
            df.at[i, 'Related Bills'] = None

        # get sponsor
        try:
            sponsor = root.findtext("./bill/sponsors/item/fullName")
            df.at[i, 'Sponsor'] = sponsor.strip() if sponsor else None
        except Exception as e:
            print(f"Failed to get sponsor for bill {number}: {e}")
            df.at[i, 'Sponsor'] = None

        # get subject
        try:
            subject = root.findtext("./bill/policyArea/name")
            df.at[i, 'Subject'] = subject.strip() if subject else None
        except Exception as e:
            print(f"Failed to get subject for bill {number}: {e}")
            df.at[i, 'Subject'] = None

        # get text access
        try:
            text_url = root.findtext("./bill/textVersions/url")
            if text_url:
                text_url = text_url.strip()
                text_root = xx.get_xml_from_link(text_url, API_KEY)
                xml_url = xx.get_url_from_text_versions(text_root)
                clean_url = xml_url.get('full text')
                df.at[i, 'Text Access'] = clean_url
            else:
                df.at[i, 'Text Access'] = None
        except Exception as e:
            print(f"Failed to get full text for record {i}: {e}")
            df.at[i, 'Text Access'] = None

    for i in range(len(df)):
        edit_df()
    
    path = f"by_congress/detailed_{congress}_laws_list.csv"
    df.to_csv(path, mode = 'w', index=False)
    print(f"Data for Congress {congress} saved to {path}")

def df_of_congress(client, congress, num):
    df = get_laws_list(client, congress, num)
    path = f"by_congress/{congress}_laws_list.csv"
    df.to_csv(path, mode='w', index=False)
    print(f"Data for Congress {congress} saved to {path}")

if __name__ == "__main__":
    # Set up API client with XML output
    client = Client(API_KEY, response_format="xml")

    df_of_congress(client, 111, 400) 
    detailed_laws_list(client, 111) 

    # commented out the above so accidently running pull_laws doesn't re run the long process