import src.config as config
from src.meilisearch import add_document, del_document
from src.gql import gql_query
import os

gql_single_collection = '''
query Collection{{
    collection(where: {{id: {ID} }}) {{
        id
        title
        status
    }}
}}
'''

def collection_handler(content):
    '''
    For collection, we only save them in Meilisearch.
    '''
    MESH_GQL_ENDPOINT = os.environ['GQL_ENDPOINT']
    memberId = content.get('memberId', config.CUSTOME_MEMBER)
    collectionId = content.get('collectionId', None)
    action = content.get('action', None)
    handler_status = False
    if memberId == 'customId' or int(memberId)<0:
        print("member is visitor")
        return handler_status
    if collectionId==None:
        print("no required collectionId for action")
        return handler_status

    try:
        if action=="add_collection":
            data, _ = gql_query(MESH_GQL_ENDPOINT, gql_single_collection.format(ID=collectionId))
            collection = data['collection']

            status = collection.get('status', None)
            if status=="publish":
                doc = [{
                    "id": collection['id'],
                    "title": collection['title']
                }]
                add_document(config.MEILISEARCH_COLLECTION_INDEX, doc)
            handler_status = True
        if action=="remove_collection":
            del_document(config.MEILISEARCH_COLLECTION_INDEX, collectionId)
            handler_status = True
    except Exception as e:
        print("collection_handler: ", str(e))
    return handler_status