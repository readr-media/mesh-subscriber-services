import os
import os
from datetime import datetime
from gql import gql, Client
from gql.transport.requests import RequestsHTTPTransport

from src.notify.query_collection import collection_follower, collection_creator_follower
from src.notify.query import creator, picker, commenter

def remove_same_member_sender(members, senderId):
    members = set(members)
    members.discard(senderId)
    return members

def query_rm_comment_data(gql_client, commentId, memberId):
    rm_comment_data = {}
    query = '''
    query{
    comment(where:{id:"%s"}){
        story{id}
        collection{id}
        root{id}
        }
    stories(where:{comment:{some:{id:{equals:%s}}}}){ 
        id
        comment(where:{id:{not:{equals:"%s"}}, is_active:{equals:true}, member:{id:{equals:"%s"}}}, orderBy:{published_date:desc}, take:1){
            published_date
            } 
        }
    collections(where:{comment:{some:{id:{equals:%s}}}}){
        id
        comment(where:{id:{not:{equals:"%s"}}, is_active:{equals:true}, member:{id:{equals:"%s"}}}, orderBy:{published_date:desc}, take:1){
            published_date
            }  
        }
    }'''% (commentId, commentId, commentId, memberId, commentId, commentId, memberId)
    result = gql_client.execute(gql(query))
    if isinstance(result, dict) and result:
        if result['comment'] and (result['comment']['story'] or result['comment']['collection']):
            if result['comment']['story']:
                rm_comment_data['obj'] = 'story'
                rm_comment_data['object_id'] = result['comment']['story']['id']
            elif result['comment']['collection']:
                rm_comment_data['obj'] = 'collection'
                rm_comment_data['object_id'] = result['comment']['collection']['id']
        else:
            return False
        if result['stories'] and result['stories'][0]['comment'] and result['stories'][0]['comment']:
            rm_comment_data['published_date'] = result['stories'][0]['comment'][0]['published_date']
        elif result['collections'] and result['collections'][0]['comment'] and result['collections'][0]['comment']:
            rm_comment_data['published_date'] = result['collections'][0]['comment'][0]['published_date']
        return rm_comment_data
    else:
        return False



def create_notify(gql_client, members, senderId, type_str, obj, objectiveId):
    now_time = datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%S.000Z")
    mutation_datas = []
    for memberId in members:
        mutation_data = '''{
            member:{
                connect:{
                    id:"%s"
                    }
                },
            sender:{
                connect:{
                    id:"%s"
                    }
                },
            type:"%s",
            objective:"%s",
            object_id:%s,
            state:"unread",
            action_date:"%s"
            }''' % (memberId, senderId, type_str, obj, objectiveId, now_time)
        mutation_datas.append(mutation_data)
    mutation_datas = ','.join(mutation_datas)
    mutation = '''
    mutation{
        createNotifies(data:[%s]){
            id
            member{
                id
            }
            sender{
                id
            }
            type
            state
            action_date
        }
    }''' % mutation_datas
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'createNotifies' in result:
        if isinstance(result['createNotifies'], list) and result['createNotifies']:
            return True
    return False

def delete_notify(gql_client,notifyId):
    delete_mutation = '''
    mutation{
        deleteNotify(where:{id:"%s"}){
            id
        }
    }''' % notifyId
    result = gql_client.execute(gql(delete_mutation))
    if isinstance(result, dict) and 'deleteNotify' in result:
        if isinstance(result['deleteNotify'], dict) and result['deleteNotify']:
            return True
    return False

def update_notifies(gql_client, notifyIds, actiondate):
    mutation_datas = []
    for notifyId in notifyIds:
        mutation_data = '''{where:{id:"%s"}data:{action_date:"%s"}}''' % (notifyId, actiondate)
        mutation_datas.append(mutation_data)
    mutation_datas = ','.join(mutation_datas)
    mutation = '''mutation{
        updateNotifies(data:[%s]){
            id
            action_date
        }
    }'''% mutation_datas
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'updateNotifies' in result:
        if isinstance(result['updateNotifies'], list) and result['updateNotifies']:
            return True
    return False


def query_members(gql_client, senderId, type_str, obj, object_id):
    if type_str == 'follow':
        if obj == 'member':
            return [object_id]
        elif obj == 'collection':
            return creator(gql_client, 'collection', 'creator', object_id)
        elif obj == 'publisher':
            return []
        else:
            print("follow objective not exists.")

    elif type_str == 'comment':
        # delete same notify before create
        notifiesId = query_delete_notifyIds(senderId, type_str, obj, object_id)
        if notifiesId:
            for notifyId in notifiesId:
                if delete_notify(notifyId):
                    continue
                else:
                    return False
        if obj == 'story':
            story_pickers = picker(gql_client, 'story', object_id)
            story_comment_members = commenter(gql_client, 'story', object_id)
            # story_picker and story_comment_member could be empty list
            return story_pickers + story_comment_members if isinstance(story_pickers, list) and isinstance(story_comment_members, list) else False

        elif obj == 'comment':
            comment_creators = creator(gql_client, 'comment', 'member', object_id)
            comment_pickers = picker(gql_client, 'comment', object_id)
            comment_members = commenter(gql_client, 'root', object_id)
            return comment_creators + comment_pickers + comment_members if comment_creators and isinstance(comment_pickers, list) and isinstance(comment_members, list) else False
        elif obj == 'collection':
            collection_creators = creator(gql_client, 'collection', 'creator', object_id)
            collection_pickers = picker(gql_client, 'collection', object_id)
            collection_comment_members = commenter(gql_client, list_name='collection', targetId=object_id)
            return collection_creators + collection_pickers + collection_comment_members if collection_creators and isinstance(collection_pickers, list) and isinstance(collection_comment_members, list) else False

        else:
            print('comment objective not exists')

    elif type_str == 'pick':
        if obj == 'comment':
            return creator(gql_client, 'comment', 'member', object_id)
        elif obj == 'collection':
            collection_creators = creator(gql_client, 'collection', 'creator', object_id)
            collection_followers = collection_follower(object_id, gql_client)
            # collection__creator must exists or this is a query error # collection_follower could be a empty list
            return collection_creators + collection_followers if collection_creators and isinstance(collection_followers, list) else False
        elif obj == 'story':
            return []
        else:
            print("pick objective not exists.")
    elif type_str == 'heart':
        return creator(gql_client, 'comment', 'member', object_id)
    elif type_str == 'create_collection':
        return collection_creator_follower(senderId, gql_client)
    elif type_str == 'pickandcomment':
        if obj == 'story':
            story_pickers = picker(gql_client, 'story', object_id)
            story_comment_members = commenter(gql_client, 'story', object_id)
            # story_picker and story_comment_member could be empty list
            return story_pickers + story_comment_members if isinstance(story_pickers, list) and isinstance(story_comment_members, list) else False

        elif obj == 'comment':
            comment_creators = creator(gql_client, 'comment', 'member', object_id)
            comment_pickers = picker(gql_client, 'comment', object_id)
            comment_members = commenter(gql_client, 'root', object_id)
            return comment_creators + comment_pickers + comment_members if comment_creators and isinstance(comment_pickers, list) and isinstance(comment_members, list) else False
        elif obj == 'collection':
            collection_creators = creator(gql_client, 'collection', 'creator', object_id)
            collection_pickers = picker(gql_client, 'collection', object_id)
            collection_comment_members = commenter(gql_client, list_name='collection', targetId=object_id)
            collection_followers = collection_follower(object_id, gql_client)
            return collection_creators + collection_pickers + collection_comment_members +collection_followers if collection_creators and isinstance(collection_pickers, list) and isinstance(collection_comment_members, list) and isinstance(collection_followers, list) else False
        else:
            print('pickandcomment objective not exists')
    else:
        print("action type not exists.")
        return False
def query_delete_notifyIds(gql_client, senderId, type_str, obj, object_id):
    query_notifiesId = '''
    query{
        notifies(where:{sender:{id:{equals:"%s"}}, type:{equals:"%s"}, objective:{equals:"%s"}, object_id:{equals:%s}}){
            id
        }
    }''' % (senderId, type_str, obj, object_id)
    result = gql_client.execute(gql(query_notifiesId))
    if isinstance(result, dict) and 'notifies' in result:
        if isinstance(result['notifies'], list):
            if result['notifies']:
                return [notifies['id']for notifies in result['notifies']]
            return []
    return False

def execute(content):
    gql_endpoint = os.environ['GQL_ENDPOINT']
    gql_transport = RequestsHTTPTransport(url=gql_endpoint)
    gql_client = Client(transport=gql_transport, fetch_schema_from_transport=True)
    
    act, *type_str = tuple(content['action'].split('_')) if 'action' in content and content['action'] else False
    type_str = "".join(type_str)
    senderId = content.get('memberId', -1)
    if int(senderId) < 0:
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
    if content['action'] == 'remove_comment':
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
            return create_notify(members, senderId, type_str, obj, object_id)
        else:
            print("No members.")
            return True
    if act == 'remove':
        notifyIds = query_delete_notifyIds(gql_client, senderId, type_str, obj, object_id)
        if notifyIds is False:
            return False
        if notifyIds:
            # check is there any comment from same sender in same 
            if type_str == 'comment'and 'published_date' in rm_comment_data:
                return update_notifies(gql_client, notifyIds, rm_comment_data['published_date'])
            for notifyId in notifyIds:
                if delete_notify(gql_client, notifyId):
                    continue
                else:
                    return False 
        return True