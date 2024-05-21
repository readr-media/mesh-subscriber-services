import datetime
from gql import gql

def check_pick_exists(memberId, storyId, gql_client):

    query = '''
            query{
                picks(where:{member:{id:{in:%s}}, story:{id:{in:%s}}, kind:{equals:"bookmark"}}, orderBy:{id:desc}){
                    id
                }
            }''' % (memberId, storyId)
    result = gql_client.execute(gql(query))
    if isinstance(result, dict) and 'picks' in result:
        if isinstance(result['picks'], list):
            return result['picks']
    return False

def add_bookmark_mutation(content, gql_client):
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    storyId = content['storyId'] if 'storyId' in content and content['storyId'] else False
    picked_date = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    if not(memberId and storyId):
        print("no required data for action")
        return False

    check_picks = check_pick_exists(memberId, storyId, gql_client)
    if check_picks == []:  # bookmark not exitsts create new pick
        mutation = '''
            mutation{
                createPick(data:{
                    member:{connect:{id:%s}}, 
                    objective:"story", 
                    story:{connect:{id:%s}}, 
                    kind:"bookmark",
                    state:"private",
                    is_active:true,
                    picked_date:"%s",                     
                }){
                    id
                    kind                             
                }
            }
        ''' % (memberId, storyId, picked_date)

    elif check_picks:  # bookmark in pick already existed
        pickId = check_picks[0]['id']
        update_data = '{where:{id:%s}, data:{is_active:true}}' % (pickId)
        mutation = '''
        mutation{
            updatePicks(data:[%s]){
                id
                is_active
                }
            }
        ''' % (update_data)
    else:
        print("query picks failed")
        return False
    result = gql_client.execute(gql(mutation))
    return True if isinstance(result, dict) and 'createPick' in result or 'updatePicks' else False


def rm_bookmark_mutation(content, gql_client):
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    storyId = content['storyId'] if 'storyId' in content and content['storyId'] else False

    if not(memberId and storyId):
        print("no required data for action")
        return False

    check_picks = check_pick_exists(memberId, storyId, gql_client)
    if check_picks:
        update_data = []
        for pick in check_picks:
            picksId = pick['id']
            update_data.append(
                '{where:{id:%s}, data:{is_active:false}}' % (picksId))
        update_data = ', '.join(update_data)
        mutation = '''
            mutation{
                    updatePicks(data:[%s]){
                        id
                        kind
                        is_active
                    }
                    }''' % (update_data)
    else:
        print("query picks failed or remove bookmark not exists")
        return False
    result = gql_client.execute(gql(mutation))
    return True if isinstance(result, dict) and 'createPick' in result or 'updatePicks' else False

def bookmark_handler(content, gql_client):
    if content['action'] == 'add_bookmark':
        return add_bookmark_mutation(content, gql_client)
    elif content['action'] == 'remove_bookmark':
        return rm_bookmark_mutation(content, gql_client)
    else:
        print("action not exitsts")
        return False