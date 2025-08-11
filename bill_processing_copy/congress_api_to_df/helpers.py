from lxml import etree
import requests

def get_tree_from_link(url, api_key=None):

    '''
    Returns the whole tree of the xml.
    '''

    try:
        # Add API key if provided
        params = {}
        if api_key:
            params['api_key'] = api_key
        
        # Fetch XML from the URL with authentication
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse the XML content
        return response.content

    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None
    except etree.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def get_room_from_link(url, api_key=None):

    '''
    Returns the root element of the xml.
    '''

    try:
        # Add API key if provided
        params = {}
        if api_key:
            params['api_key'] = api_key
        
        # Fetch XML from the URL with authentication
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse the XML content
        root = etree.fromstring(response.content)
        return root

    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None
    except etree.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None

def get_xml_from_link(url, api_key=None):

    '''
    Returns the root of the xml tree.
    '''

    try:
        # Add API key if provided
        params = {}
        if api_key:
            params['api_key'] = api_key
        
        # Fetch XML from the URL with authentication
        response = requests.get(url, params=params)
        response.raise_for_status()

        # Parse the XML content
        root = etree.fromstring(response.content)
        return root

    except requests.exceptions.RequestException as e:
        print(f"Error fetching XML: {e}")
        return None
    except etree.ParseError as e:
        print(f"Error parsing XML: {e}")
        return None
    
def print_clean_xml(elem, level=0):

    '''
    Root is parameter.
    '''

    indent = '  ' * level
    print(f"{indent}<{elem.tag}>")
    
    # Print text if present and not just whitespace
    if elem.text and elem.text.strip():
        print(f"{indent}  {elem.text.strip()}")

    # Recurse on children
    for child in elem:
        print_clean_xml(child, level + 1)

    print(f"{indent}</{elem.tag}>")

def length(root):
    element_count = len(list(root.iter(tag=etree.Element)))
    return element_count


def get_url_from_text_versions(root):
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
            if ('formatted xml' in current_type):
                
                url_elem = format_item.find('url')
                if url_elem is not None and url_elem.text:
                    url =  url_elem.text.strip()
                
                    url_dict = {}
                    url_dict['full text'] = url

                    return url_dict
    
    return None