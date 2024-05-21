from gql import gql
 
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