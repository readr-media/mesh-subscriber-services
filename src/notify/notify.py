import os
from gql import Client
from gql.transport.requests import RequestsHTTPTransport

from src.notify.query import query_rm_comment_data, query_members, remove_same_member_sender, query_delete_notifyIds, update_notifies, delete_notify, create_notify
import src.config as config

from src.notify.follow import notify_add_follow
from src.notify.comment import notify_add_comment
from src.notify.pick import notify_add_pick
from src.notify.collection import notify_add_collection
from src.notify.like import notify_add_like
from src.mongo import connect_db

def validate_input(data: dict):
    action = data.get('action', "None")
    objective = data.get('objective', "None")
    if action not in config.VALID_NOTIFY_ACTIONS.keys():
        return False
    valid_objs = config.VALID_NOTIFY_ACTIONS[action]
    if objective not in valid_objs:
        return False
    return True

def execute_mongo(content):
    # check input
    if validate_input(content)==False:
        return False
    action = content.get('action', None)
    
    # connect mongodb
    mongo_url = os.environ.get('MONGO_URL', None)
    env = os.environ.get('ENV', 'dev')
    db = connect_db(mongo_url, env)
    
    # assing tasks
    result = True
    if action=="add_follow":
        result = notify_add_follow(db, content)
    if action=="add_comment":
        result = notify_add_comment(db, content)
    if action=="add_pick_and_comment":
        ### notification of add_pick_and_comment is equals to add_comment
        content['action'] = 'add_comment'
        result = notify_add_comment(db, content)
    if action=="add_pick":
        result = notify_add_pick(db, content)
    if action=="add_like":
        result = notify_add_like(db, content)
    if action=="add_collection":
        result = notify_add_collection(db, content)
    return result


def execute_cms(content):
    '''
        Execute notification processing and write into CMS
    '''
    gql_endpoint = os.environ['GQL_ENDPOINT']
    gql_transport = RequestsHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)

    action = content.get('action', False)
    act, *type_str = tuple(content['action'].split('_')) if action else False
    type_str = "".join(type_str)
    senderId = content.get('memberId', config.CUSTOME_MEMBER)
    if senderId=='customId' or int(senderId) < 0:
        print("memberId is visitor")
        return True
    
    # object_id assignment
    object_id = (
        content.get('targetId', '') or \
        content.get('commentId', '') or \
        content.get('storyId', '') or \
        content.get('collectionId', '')
    )
    if object_id=='':
        return False
    
    # remove_comment has different data
    if action == 'remove_comment':
        rm_comment_data = query_rm_comment_data(gql_client, object_id, senderId)
        if rm_comment_data:
            obj = rm_comment_data['obj']
            object_id = rm_comment_data['object_id']
    else:
        if content.get('objective', ''):
            obj = content['objective']
        elif type_str == 'like':
            type_str = 'heart'
            obj = 'comment'
        elif type_str == 'collection':
            type_str = 'create_collection'
            obj = 'collection'
        else:
            return False
        if not(senderId and type_str):
            print("no required data for notify")
            return False
    
    if act == 'add':
        members = query_members(gql_client, senderId, type_str, obj, object_id)
        if type_str == 'pickandcomment':
            type_str = 'pick'
        if members is False:
            return False
        members = remove_same_member_sender(members, senderId)
        if members:
            return create_notify(gql_client, members, senderId, type_str, obj, object_id)
        else:
            print("No members.")
            return True
    if act == 'remove':
        notifyIds = query_delete_notifyIds(gql_client, senderId, type_str, obj, object_id)
        if len(notifyIds)==0:
            return False
        else:
            # check is there any comment from same sender in same 
            if type_str == 'comment'and 'published_date' in rm_comment_data:
                return update_notifies(gql_client, notifyIds, rm_comment_data['published_date'])
            for notifyId in notifyIds:
                if delete_notify(gql_client, notifyId):
                    continue
                else:
                    return False 
        return True
