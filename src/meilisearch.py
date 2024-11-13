import os
import meilisearch
import gql
from src.config import MEILISEARCH_MEMBER_INDEX

gql_member_search = '''
query Member{{
    member(where: {{id: {ID} }}){{
        id
        name
    }}
}}
'''

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
        
def add_member(member_id, gql_client):
    data = gql_client.execute(gql(gql_member_search.format(ID=member_id)))
    member = data['member']
    if member:
        add_document(MEILISEARCH_MEMBER_INDEX, [member])
        return True
    print("update member failed to meilisearch")
    return False

def del_member(member_id):
    del_document(MEILISEARCH_MEMBER_INDEX, member_id)
    return True