from gql import gql
import src.config as config

def like_handler(content, gql_client):
    memberId = content.get('memberId', config.CUSTOME_MEMBER)
    if memberId == 'customId' or int(memberId)<0:
        print("member is visitor")
        return True
    commentId = content['commentId'] if 'commentId' in content and content['commentId'] else False
    
    if not(memberId and commentId):
        print("no required data for action")
        return False

    if content['action'] == 'add_like':
        action = 'connect'
    elif content['action'] == 'remove_like':
        action = 'disconnect'
    else:
        print("action not exitsts")
        return False
    
    mutation = '''
            mutation{
            updateComment(where:{id:"%s"}, data:{like:{%s:{id:%s}}}){
                like{
                id
                }
            }
            
            }''' % (commentId,action, memberId)
    result = gql_client.execute(gql(mutation))
    return True if isinstance(result, dict) and 'updateComment' in result  else False