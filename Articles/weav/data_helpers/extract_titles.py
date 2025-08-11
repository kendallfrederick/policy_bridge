import os
from lxml import etree as et
import ollama
import weaviate

data_path = "/Users/intern7/Policy_Project/plosone/"

#1064 ~ 1065
with open("plosone_titles.txt", "a") as record:
    for i in range(2):
        folder = data_path + str(i)
        record.write("Articles from folder " + str(i) + ":\n")

        for xml_path in (path for path in os.scandir(folder) if not path.name.startswith('.')):
            full_path = folder + "/" + xml_path.name
            try:
                tree = et.parse(full_path)
                root = tree.getroot()

                # Parse article metadata from xml to add parent object to article_meta collection
                meta = root.find("front/article-meta")
                title_el = meta.find("title-group/article-title")
                title = title_el.xpath("string()")
                
                record.write("(" + str(i) + ") " + title + "\n")
            except et.ParseError as e:
                print(f"Error: Could not parse xml file: {e} from path {full_path}")
            except FileNotFoundError:
                print(f"Error: Could not find the file at path {full_path}")
                
        record.write("\n\n")
record.close()