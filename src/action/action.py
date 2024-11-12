import os
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from src.action.follow import follow_handler
from src.action.comment import comment_handler
from src.action.pick import pick_handler
from src.action.bookmark import bookmark_handler
from src.action.like import like_handler
from src.action.category import category_handler
from src.action.member import member_handler
from src.action.collection import collection_handler

def execute(content):
    if 'action' in content and content['action']:
        action = content['action']
        gql_endpoint = os.environ['GQL_ENDPOINT']
        gql_transport = RequestsHTTPTransport(url=gql_endpoint)
        gql_client = Client(transport=gql_transport,
                            fetch_schema_from_transport=True)
        if 'follow' in action:
            return follow_handler(content, gql_client)
        if 'pick' in action:
            return pick_handler(content, gql_client)
        if 'comment' in action:
            return comment_handler(content, gql_client)
        if 'bookmark' in action:
            return bookmark_handler(content, gql_client)
        if 'like' in action:
            return like_handler(content, gql_client)
        if 'category' in action:
            return category_handler(content, gql_client)
        if 'member' in action:
            return member_handler(content, gql_client)
        if 'collection' in action:
            return collection_handler(content)
        if 'read' in action:
            return True
    return False