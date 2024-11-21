from gql import gql
from datetime import datetime

def picker(gql_client, list_name, targetId):
    membersId = []
    picker_script = '''
    query{
        picks(where:{%s:{id:{equals:"%s"}}, kind:{equals:"read"}, is_active:{equals:true}}){
            member{
                id
            }
        }
    }
    '''% (list_name, targetId)
    result = gql_client.execute(gql(picker_script))
    if isinstance(result,dict) and 'picks' in result:
        if isinstance(result['picks'],list):
            picks = result['picks']
            if picks:
                for pick in picks:
                    if 'member' in pick and pick['member']:
                        membersId.append(pick['member']['id'])
                    else:
                        print(f"query error in {list_name}_picker")
                        return False
            else:
                print("no pick exists.")# it will return empty list           
            return membersId
    print(f"query error in {list_name}_picker.")
    return False

def commenter(gql_client, list_name, targetId):
    membersId = []
    picker_script = '''
    query{
            comments(where:{%s:{id:{equals:"%s"}}, is_active:{equals:true}}){
            member{
                id
                }
            }
    }'''% (list_name, targetId)
    result = gql_client.execute(gql(picker_script))
    if isinstance(result,dict) and 'comments' in result:
        if isinstance(result['comments'],list):
            comments = result['comments']
            if comments:
                for comment in comments:
                    if 'member' in comment and comment['member']:
                        membersId.append(comment['member']['id'])
                    else:
                        print(f"query error in {list_name}_comments")
                        return False
            else:
                print("no comment exists.")# it will return empty list           
            return membersId
    print(f"query error in {list_name}_commenter.")
    return False


def creator(gql_client, list_name, creator_field_name, targetId):
    creator_script = '''
    query{
            %s(where:{id:"%s"}){
                %s{
                    id
                }
            }
        }
    '''%(list_name, targetId, creator_field_name)
    result = gql_client.execute(gql(creator_script))
    if isinstance(result,dict) and list_name in result :
        if isinstance(result[list_name],dict) and creator_field_name in result[list_name]:
            creator = result[list_name][creator_field_name]
            if creator:
                return [creator['id']]
    print(f"query error in {list_name}_creator.")
    return False


def collection_follower(collectionId, gql_client):
    membersId = []
    collection_follower = '''
        query{
            members(where:{following_collection:{some:{id:{equals:"%s"}}}}){
                id
                }
        }'''% collectionId
    result = gql_client.execute(gql(collection_follower))
    if isinstance(result,dict) and 'members' in result:
        if isinstance(result['members'],list):
            members = result['members']
            if members:
                for member in  members:
                    membersId.append(member['id'])
            else:
                print("no member following this collection")# it will return empty list
            return membersId
    print("query error in collection_follower")
    return False

def collection_creator_follower(senderId, gql_client):
    membersId = []
    collection_creator_follower = '''
    query{
        member(where:{id:%s}){
            follower{
                id
            }
        }
    }''' % senderId
    result = gql_client.execute(gql(collection_creator_follower))
    if isinstance(result,dict) and 'member' in result:
        if isinstance(result['member'],dict) and 'follower' in result['member']: 
            member = result['member']
            if isinstance(member['follower'],list):
                followers = member['follower']
                if followers:
                    for follower in  followers:
                        membersId.append(follower['id'])
                else:
                    print("no member following this member")# it will return empty list
                return membersId
    print("query error in collection_creator_follower.")
    return False

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

def delete_notify(gql_client, notifyId: int=None):
    if notifyId:
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
        notifiesId = query_delete_notifyIds(gql_client, senderId, type_str, obj, object_id)
        if len(notifiesId)==0:
            return False
        for notifyId in notifiesId:
            if delete_notify(gql_client, notifyId):
                continue
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
    return []