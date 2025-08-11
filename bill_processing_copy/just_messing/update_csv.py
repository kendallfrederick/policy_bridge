import pandas as pd
import numpy as np
from lxml import etree
import requests

import helpers as xx

from api_client import Client
API_KEY = 'qo7lPHj8lcYm7TK9tEGascFIhm1cWqeZ9PJyxPEh'
    

if __name__ == "__main__":

    client = Client(API_KEY, response_format="xml")

    df = pd.read_csv('laws_list.csv')
    #df = pd.read_csv('updated_list.csv')

    #create new column for subject and initialize to NaN ONLY WHEN STARTING FRESH CSV
    df['Sponsor'] = None
    df['Subject'] = None
    df['Text Access'] = None

    print(df.head)

    # get the url for the bills info from the stored dataframe
    # 0 is first row, currently goes up to 19
    '''
    n = df.at[0,'Number'].item()
    t = df.at[0,'Type']
    c = df.at[0,'Congress'].item()

    data = get_bill_subjects(client, c, t, n)
    print(data)
    '''

    for i in range(643):
        try:
            url = df.at[i,'Url']
            num = df.at[i,'Url']
            print(f"{num}\n\n\n")
            root = xx.get_xml_from_link(url, API_KEY)
            
            # get the senator/ congressperson sponsoring the bill
            try:
                sponsor = root.findtext("./bill/sponsors/item/fullName")
                if sponsor:
                    sponsor = sponsor.strip()
                    print(sponsor)
                    df.at[i,'Sponsor'] = sponsor
            except:
                df.at[i,'Sponsor'] = None
            
            # get the subject area of the bill
            try:
                area = root.findtext("./bill/policyArea/name")
                if area:
                    area = area.strip()
                    print(area)
                    df.at[i,'Subject'] = area
            except:
                df.at[i,'Subject'] = None
            
            # get the url to the text version of the bill
            try:
                text_url = root.findtext("./bill/textVersions/url").strip()
                text_root = xx.get_xml_from_link(text_url, API_KEY)
                xml_url = xx.get_url_from_text_versions(text_root)
                clean_url = xml_url['full text']
                df.at[i,'Text Access'] = clean_url
            except:
                print(f"Failed to get full text for record {i}")
                continue
                
        except Exception as e:
            print(f"Error processing record {i}: {e}")
            continue


#df.to_csv('updated_list.csv', index=False)

#full_root = xx.get_xml_from_link(clean_url, API_KEY)

    