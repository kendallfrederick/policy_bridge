import os
from lxml import etree as et

data_path = '/Users/law/Journals/plosclimate'
count = 1

for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    full_path = data_path + '/' + xml_path.name

    if count == 117:
        tree = et.parse(full_path)
        root = tree.getroot()

        # Parse article metadata from xml to add parent object to article_meta collection
        meta = root.find('front/article-meta')
        doi = meta.findtext('article-id[@pub-id-type="doi"]')

        print(doi)
    
    count = count + 1