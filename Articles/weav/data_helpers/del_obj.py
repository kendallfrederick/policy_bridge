import weaviate
from weaviate.classes.query import Filter

client = weaviate.connect_to_local()
collection = client.collections.get('xmls')

collection.data.delete_many(
    where=Filter.by_property('doi').contains_any(['10.3390/cli7050070'])
)

client.close()