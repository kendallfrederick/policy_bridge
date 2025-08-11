import webbrowser
import weaviate
from weaviate.collections.classes.filters import Filter

client = weaviate.connect_to_local()
collection = client.collections.get('xmls')

where=Filter.by_property('title').contains_any(['Characterizing echo chambers'])

obj_info = collection.query.fetch_objects(
        filters=where,
        return_properties=['doi']
    )

for obj in obj_info.objects:
    doi = obj.properties['doi']
    doi_addr = f'https://doi.org/{doi}'
    webbrowser.open(doi_addr)
    
client.close()