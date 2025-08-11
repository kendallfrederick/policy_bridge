import os
import xml.etree.ElementTree as et
import ollama
import weaviate
from weaviate.classes.config import Property, DataType
import warnings

warnings.filterwarnings("ignore", category=ResourceWarning)

data_path = '/Users/law/Articles/data_folders/2'

for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    name = xml_path.name
    print(f'{name}\n')