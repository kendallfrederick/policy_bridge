import os
import shutil

data_path = '/opt/anaconda3/lib/python3.12/site-packages/allofplos/allofplos_xml'
dest_dir = '/Users/law/Articles/data_folders/0'
os.makedirs(dest_dir)
folder = 0
size = 0

for xml_path in (path for path in os.scandir(data_path) if not path.name.startswith('.')):
    if size == 1000:
        folder = folder + 1
        size = 0
        dest_dir = '/Users/law/Articles/data_folders/' + str(folder)
        os.makedirs(dest_dir)

    src_path = data_path + '/' + xml_path.name
    dest_path = os.path.join(dest_dir, os.path.basename(src_path))
    shutil.copy(src_path, dest_path)

    size = size + 1
