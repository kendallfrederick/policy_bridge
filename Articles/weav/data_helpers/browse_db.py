import weaviate

client = weaviate.connect_to_local()

collection = client.collections.get('articles')

'''
objects = collection.query.fetch_objects(limit=4600)
count = 0
for o in objects.objects:
    if count > 4500:
        print(o.properties['title'])
    count = count + 1
'''

count = collection.aggregate.over_all(
    total_count=True
)
print(count.total_count)


client.close()