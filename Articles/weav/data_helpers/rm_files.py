import os

data_path = '/Users/law/Articles/data_folders/3'
count = 0

for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    if count == 29:
        print(xml_path)

    #full_path = data_path + '/' + xml_path.name
    #os.remove(full_path)
    count = count + 1
