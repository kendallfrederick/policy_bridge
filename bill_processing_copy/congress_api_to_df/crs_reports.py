import xml.etree.ElementTree as ET
from api_client import Client

import helpers as xx

import pandas as pd

# Constants
API_KEY = 'qo7lPHj8lcYm7TK9tEGascFIhm1cWqeZ9PJyxPEh' # i know this is bad and i'm sorry

climate_crs_reports = ['TE10101','R48258','IF11696','IF12433','IF12636','R48480','IF12753','IN11696']

def get_crs_list(client):

    all_data = []

    endpoint = f"crsreport?limit=10?offset=10"
    crs_list = client.get(endpoint)

    print(crs_list)
    print(type(crs_list))

    bytes = crs_list[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    status = [crs.text.strip() for crs in root.findall('./CRSReports/item/status')]
    id = [crs.text.strip() for crs in root.findall('./CRSReports/item/id')]
    crs = [crs.text.strip() for crs in root.findall('./CRSReports/item/contentType')]
    title = [crs.text.strip() for crs in root.findall('./CRSReports/item/title')]
    url = [crs.text.strip() for crs in root.findall('./CRSReports/item/url')]

    # Transpose and append
    batch_data = list(zip(status, id, crs, title, url))
    all_data.extend(batch_data)

    df = pd.DataFrame(all_data, columns=['status', 'id', 'content_type', 'title', 'url'])
    return df

def get_climate_list(client, climate_list):

    all_data = []

    for id in climate_list:

        endpoint = f"crsreport/{id}"
        crs_list = client.get(endpoint)

        bytes = crs_list[0]
        string = bytes.decode('utf-8')
        root = ET.fromstring(string)

        id = [crs.text.strip() for crs in root.findall('./CRSReport/id')]
        date = [crs.text.strip() for crs in root.findall('./CRSReport/publishDate')]
        update = [crs.text.strip() for crs in root.findall('./CRSReport/updateDate')]
        title = [crs.text.strip() for crs in root.findall('./CRSReport/title')]
        summary = [crs.text.strip() for crs in root.findall('./CRSReport/summary')]
        pdf = ["none found"]
        for item in root.findall('./CRSReport/formats/item'):
            format_elem = item.find('format')
            url_elem = item.find('url')
            if format_elem is not None and format_elem.text and format_elem.text.strip() == 'PDF':
                if url_elem is not None and url_elem.text:
                    pdf = [url_elem.text.strip()]
                    print(f"title: {title}, pdf: {pdf}")
                    break
            
        # Transpose and append
        batch_data = list(zip(id, date, update, title, summary, pdf))
        all_data.extend(batch_data)

    df = pd.DataFrame(all_data, columns=['id', 'date', 'update', 'title', 'summary','pdf'])
    return df

def get_crs_report(client,id):

    all_data = []

    endpoint = f"crsreport/{id}"
    crs = client.get(endpoint)

    bytes = crs[0]
    string = bytes.decode('utf-8')
    root = ET.fromstring(string)

    print_clean_xml(root)

    status = [crs.text.strip() for crs in root.findall('./CRSReports/item/status')]
    id = [crs.text.strip() for crs in root.findall('./CRSReports/item/id')]
    crs = [crs.text.strip() for crs in root.findall('./CRSReports/item/contentType')]
    title = [crs.text.strip() for crs in root.findall('./CRSReports/item/title')]
    url = [crs.text.strip() for crs in root.findall('./CRSReports/item/url')]

    # Transpose and append
    batch_data = list(zip(status, id, crs, title, url))
    all_data.extend(batch_data)

    df = pd.DataFrame(all_data, columns=['status', 'id', 'content_type', 'title', 'url'])
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

def df_of_crs_reports(client,climate_list):
    df = get_climate_list(client,climate_list)
    path = f"crs/ai.csv"
    df.to_csv(path, mode='a', index=False)
    print(f"Data saved to {path}")

if __name__ == "__main__":
    # Set up API client with XML output
    client = Client(API_KEY, response_format="xml")

    #df_of_crs_reports(client) 

    climate_24_25 = ['TE10101','R48258','IF11696','IF12433','IF12636','R48480','IF12753','IN11696']
    climate_22_23 = ['R46766','IN12250','IF12161','R47063',
                    'IN12288','IF12282','IF12178','R47583',
                    'R47551','R47082','IF11921','IF12300',
                    'IF12043','IF12324','R47262']
    climate_20_21 = ['R46743','R46694','R46585','R46454','IN11666','IF11827','IF11815','R46947',
                     'IF11446','IF11693','R46452','IN11545','IF11103','R46204','IF11746','R45086',
                     'LSB10605','R42405','R45745','R46323','IN11227','R46312']
    
    ai_24_25 = ['R48319','R47997','LSB11251','LSB11052','IN12458','IN12222','IG10077',
                'R48555','LSB10922','IF12426','IF12762','IN12537','R47843','IF12899'] # 14 total

    ai_22_23 = ['R47849','R47644','IF12468','R47569','IF12399','IF12497','IN12289','LSB11097'] # 8 total

    ai_20_21 = ['R46795','R45178']

    # get_crs_report(client, 'TE10101')
    df_of_crs_reports(client, ai_20_21)