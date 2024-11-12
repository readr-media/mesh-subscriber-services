import os
import meilisearch

def add_document(index, data):
    '''
      Store data into Meilisearch index. data should be a list with dict content.
    '''
    meilisearch_host = os.environ['MEILISEARCH_HOST']
    meilisearch_apikey = os.environ['MEILISEARCH_APIKEY']
    client = meilisearch.Client( meilisearch_host, meilisearch_apikey)
    try:
        client.index(index).add_documents(data)
    except Exception as e:
        print(f'add document failed, reason: {e}')
        
def del_document(index, document_id):
    meilisearch_host = os.environ['MEILISEARCH_HOST']
    meilisearch_apikey = os.environ['MEILISEARCH_APIKEY']
    client = meilisearch.Client( meilisearch_host, meilisearch_apikey)
    try:
        client.index(index).delete_document(document_id)
    except Exception as e:
        print(f'add document failed, reason: {e}') 