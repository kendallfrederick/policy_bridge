import xml.etree.ElementTree as ET
from api_client import Client
import requests
import webbrowser

# Constants
CONGRESS = 118
BILL_HR = "hr"
BILL_NUM = 7192
API_KEY = 'qo7lPHj8lcYm7TK9tEGascFIhm1cWqeZ9PJyxPEh'

### current version works on enrolled bills
'''
 118: 1, 2, 5, 7
'''

def get_bill_text(client):
    """
    'https://api.congress.gov/v3/bill/117/hr/21/text'
    This API returns, text versions of the specified Bill
    as urls
    """
    endpoint = f"bill/{CONGRESS}/{BILL_HR}/{BILL_NUM}/text"
    data = client.get(endpoint)
    
    return data

def get_bill_summaries(client):
    """
    'https://api.congress.gov/v3/bill/117/hr/21/summaries'
    This API returns, summaries of the specified Bill
    Bill subjects
    """
    endpoint = f"bill/{CONGRESS}/{BILL_HR}/{BILL_NUM}/summaries"
    data = client.get(endpoint)

    return data

def get_laws_list(client):
    endpoint = f"law/{CONGRESS}"
    law_list = client.get(endpoint)

    return law_list

def get_url(xml_string, format_type='xml'):
    """
    Extract URL from Congress.gov bill text XML.
    
    Args:
        xml_string (str): XML response from Congress.gov API
        format_type (str): Format type ('htm', 'pdf', 'xml')
    
    Returns:
        str: URL for the requested format
    """
    if not isinstance(xml_string, str):
        raise TypeError("xml_string must be a string")
    
    try:
        root = ET.fromstring(xml_string)
    except ET.ParseError as e:
        raise ET.ParseError(f"Invalid XML: {e}")
    
    # Try to get URL from textVersions first
    url = _get_url_from_text_versions(root, format_type)
    if url:
        return url
    
    print(f"\n was not able to get url from textVersions\n")
    # Fallback to request section
    return _get_url_from_request(root)


def _get_url_from_text_versions(root, format_type):
    """Get URL from textVersions/item/formats structure."""
    text_versions = root.find('textVersions')
    if text_versions is None:
        return None
    
    # Look through all items to find "Enrolled Bill" or use first item as fallback
    enrolled_item = None
    first_item = None
    
    for item in text_versions.findall('item'):
        if first_item is None:
            first_item = item
            
        type_elem = item.find('type')
        if type_elem is not None and type_elem.text:
            if "enrolled bill" in type_elem.text.lower():
                enrolled_item = item
                break
    
    # Use enrolled bill if found, otherwise use first item
    target_item = enrolled_item if enrolled_item is not None else first_item
    if target_item is None:
        return None
    
    # Get formats from the target item
    formats = target_item.find('formats')
    if formats is None:
        return None
    
    # Find matching format type
    for format_item in formats.findall('item'):
        type_elem = format_item.find('type')
        if type_elem is not None and type_elem.text:
            current_type = type_elem.text.lower()
            
            # Match format types based on your notes:
            # "Formatted Text" = htm, "PDF" = pdf, "Formatted XML" = xml
            if ((format_type == 'htm' and 'formatted text' in current_type) or
                (format_type == 'pdf' and 'pdf' in current_type) or  
                (format_type == 'xml' and 'formatted xml' in current_type)):
                
                url_elem = format_item.find('url')
                if url_elem is not None and url_elem.text:
                    url =  url_elem.text.strip()
                
                    url_dict = {}
                    url_dict['full text'] = url

                    return url_dict
    
    return None


def _get_url_from_request(root):
    """Get URL from request/billUrl as fallback."""
    request = root.find('request')
    if request is None:
        raise ValueError("No textVersions found and no request section available")
    
    bill_url = request.find('billUrl')
    if bill_url is None or not bill_url.text:
        raise ValueError("No billUrl found in request section")
    
    url = bill_url.text.strip()

    url_dict = {}
    url_dict['summary text'] = url

    return url_dict

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

def print_nested_tags(element, indent=0):
    """
    Recursively prints the tags of an XML element and its children.

    Args:
        element: The current ElementTree element to process.
        indent: The current indentation level for pretty printing.
    """
    print("  " * indent + element.tag)
    for child in element:
        print_nested_tags(child, indent + 1)

def get_xml_from_link(url, api_key=None):

    try:
        # Add API key if provided
        params = {}
        if api_key:
            params['api_key'] = api_key
        
        # Fetch XML from the URL with authentication
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse the XML content
        root = ET.fromstring(response.content)
        return root

    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None
    except ET.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def print_metadata(root):

    # iterate metadata items
    for item in root.findall('./metadata/dublinCore'):

        # iterate child elements of item
        for child in item:

            print(f"child tag: {child.tag}")
            print(f"   child text: {child.text}\n")

def get_title(root):
    for item in root.findall('./metadata/dublinCore'):
        title = item[0].text
        print(f"title: {title}")
        return title
        
    print("didn't find title")

def get_date(root):
    """
    returns string in the form year-month-day
    for example: 2023-03-16
    
    """
    for item in root.findall('./metadata/dublinCore'):
        date = item[2].text
        print(f"date: {date}")
        return date
        
    print("didn't find date")

def get_official_title(root):
    for item in root.findall('./form/official-title'):
        print(f"official title: {item.text}")
        return item.text
    
def extract_divisons(root):
    divisions = []

    for item in root.findall('./legis-body/division/header'):
        divisions.append(item.text)

    return divisions

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

def extract_relevant_text(elem):
    lines = []

    def recurse(e):
        if e.tag == "header":
            lines.append(f"\n{e.text.strip()}\n" if e.text else "")
        elif e.tag == "paragraph":
            enum = e.find("enum")
            text = e.find("text")
            claim = f"{enum.text.strip()} {text.text.strip()}" if enum is not None and text is not None else ""
            if claim:
                lines.append(claim)
        '''
        elif e.tag == "text" and e.text and e.text.strip():
            lines.append(e.text.strip())
        '''
        for child in e:
            recurse(child)

    recurse(elem)
    return '\n'.join(lines)


def explore_content(root):
    get_title(root)
    get_date(root)
    get_official_title(root)

    divisions = extract_divisons(root)

    #print_nested_tags(root)
    '''
    i = 0
    for item in root.findall('./legis-body/section/subsection'):
        if i < 1:
            #string = print_clean_xml(item)
            string = extract_relevant_text(item)
            print(f"{string}\n")
        i += 1
    '''

    print_clean_xml(root)

    target = next(
        (item for item in root.findall('./legis-body/section/subsection')
        if (item.find('header') is not None and item.find('header').text.strip().lower() == 'findings')),
        None
    )

    if target is not None:
        string = extract_relevant_text(target)
        print(f"{string}\n")

    
    '''
    for item in root.findall('./legis-body/division'):
        for child in item:
            print(f"child tag: {child.tag}")
            print(f"child text: {child.text}")
            for grandchild in child:
                print(f"   gchild tag: {grandchild.tag}")
                print(f"   gchild text: {grandchild.text}")
    '''
    


if __name__ == "__main__":
    # Set up API client with XML output
    client = Client(API_KEY, response_format="xml")
    
    data = get_bill_summaries(client)
    print(data)

    # laws = get_laws_list(client)
    # bytes = laws[0]
    # string = bytes.decode('utf-8')

    # num_laws = laws[1]

    # print(num_laws)

    # root = ET.fromstring(string)

    # print_clean_xml(root)


    '''
    
    tuple = get_bill_text(client)
    bytes = tuple[0] # bytes type
    string = bytes.decode('utf-8')


    url_dict = get_url(string)

    if list(url_dict.keys())[0] == 'full text':
        print(f"got all text!\n")
        url1 = url_dict['full text']
    elif list(url_dict.keys())[0] == 'summary text':
        print(f"got other version\n")
        url1 = url_dict['summary text']

    #url2 = get_url_orig(string,'xml')
    #open_url_in_browser(url1)
    #open_url_in_browser(url2)

    root = get_xml_from_link(url1, API_KEY)
    
    #print_nested_tags(root)

    print(f"url1: {url1}\n")

    #print_metadata(root)
    

    #explore_content(root)
    
    '''
    



    

    '''
        for child in formats:
            url = child.find('url')
            type = child.find('type')
            
            print(f"{type.text}: {url.text}\n")
    '''
            
    '''
        print(f"child: {child.tag}")
        enrolled = child[0]
            print(f"   {enrolled.tag}")
            formats = enrolled[2]
            print(f"      {formats.tag}")
            url = formats[0][0]
            print(f"         {url.tag}")
            print(f"         {url.attrib}")
        
            for x in child:
                print(f"   x: {x.tag}")
                for y in x:
                    print(f"      y: {y.tag}")
                    for z in y:
                            print(f"         {z.attrib}")
            '''
            


    '''
    textVersions
        item
            type Enrolled Bill
            formats
                item
                    url .htm !!!!!
                    type Formatted Text 
                item
                    url .pdf
                    type PDF
                item
                    url .xml
                    type Formatted XML
            type Placed on Calendar Senate
                ...

    
    '''
