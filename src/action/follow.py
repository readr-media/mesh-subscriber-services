from gql import gql

def follow_handler(content, gql_client):

    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    targetId = content['targetId'] if 'targetId' in content and content['targetId'] else False
    obj = content['objective'] if 'objective' in content and content['objective'] else False

    if not(memberId and targetId and obj):
        print("no required data for action")
        return False

    if obj == 'member':
        obj_following = 'following'
    elif obj == 'publisher':
        obj_following = 'follow_publisher'
    elif obj == 'collection':
        obj_following = 'following_collection'
    else:
        print("objective not exitsts")
        return False

    if content['action'] == 'add_follow':
        action = 'connect'
    elif content['action'] == 'remove_follow':
        action = 'disconnect'
    else:
        print("action not exitsts")
        return False

    mutation = '''
    mutation{
    updateMember(where:{id:%s}, data:{%s:{%s:{id:%s}}},){
        %s{
        id
        }
    }
    }''' % (memberId, obj_following, action, targetId, obj_following)
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'updateMember' in result:
        follow_item = [follow_item['id'] for follow_item in result['updateMember'][obj_following]]
        if targetId in follow_item and action == 'connect':
            return True
        if targetId not in follow_item and action == 'disconnect':
            return True
    return False