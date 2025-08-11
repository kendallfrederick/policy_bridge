import os
import shutil
import xml.etree.ElementTree as et

data_path = '/opt/anaconda3/lib/python3.12/site-packages/allofplos/allofplos_xml'
#dest_dir = '/Users/law/Journals/climate'
#os.makedirs(dest_dir, exist_ok=True)

for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    src_path = data_path + '/' + xml_path.name

    try:
        tree = et.parse(src_path)
        root = tree.getroot()
        j_meta = root.find('.//front/journal-meta')
        journal = j_meta.findtext('journal-id[@journal-id-type="pmc"]')
        dest_dir = '/Users/law/Journals/' + journal
        dest_path = os.path.join(dest_dir, os.path.basename(src_path))
        shutil.copy(src_path, dest_path)
            
    except et.ParseError as e:
        print(f'Error: Could not parse xml file: {e} from path {src_path}')
    except FileNotFoundError:
        print(f'Error: Could not find the file at path {src_path}')