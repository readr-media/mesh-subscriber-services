import datetime
from gql import gql


def add_comment_mutation(content, gql_client):
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    targetId = content['targetId'] if 'targetId' in content and content['targetId'] else False
    state = content['state'] if 'state' in content and content['state'] else False
    comment_content = content['content'].replace("\n", "\\n") if 'content' in content and content['content'] else False
    obj = content['objective'] if 'objective' in content and content['objective'] else False
    published_date = datetime.datetime.utcnow().strftime('%Y-%m-%dT%H:%M:%S.%fZ')

    if not(memberId and targetId and state and comment_content and obj):
        print("no required data for action")
        return False

    obj = 'root' if obj == 'comment' else obj

    mutation = '''
            mutation{
                createComment(data:{
                    member:{connect:{id:%s}}, 
                    %s:{connect:{id:%s}}, 
                    is_active:true, 
                    state:"%s", 
                    published_date:"%s", 
                    content:"%s"
                    })
                    {
                id
                } 
            }''' % (memberId, obj, targetId, state, published_date, comment_content)
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'createComment' in result:
        return True
    return False
def rm_comment_mutation(content, gql_client):
    commentId = content['commentId'] if 'commentId' in content and content['commentId'] else False
    if not commentId:
        print("no required data for action")
        return False

    mutation = '''
         mutation{
            updateComment(where:{id:%s}, data:{is_active:false}){
                id
                }
            }''' % (commentId)
    result = gql_client.execute(gql(mutation))
    return True if isinstance(result, dict) and 'updateComment' in result else False

def edit_comment_mutation(content, gql_client):
    commentId = content['commentId'] if 'commentId' in content and content['commentId'] else False
    comment_content = content['content'].replace("\n", "\\n") if 'content' in content and content['content'] else False
    if not (commentId and comment_content):
        print("no required data for action")
        return False
        
    mutation = '''
        mutation{
            updateComment(where:{id:%s}, data:{content:"%s", is_edited:true}){
                id
                }
            }''' % (commentId, comment_content)
    result = gql_client.execute(gql(mutation))
    return True if isinstance(result, dict) and 'updateComment' in result  else False

def comment_handler(content, gql_client):

    if content['action'] == 'add_comment':
        return add_comment_mutation(content, gql_client)
    elif content['action'] == 'remove_comment':
        return rm_comment_mutation(content, gql_client)
    elif content['action'] == 'edit_comment':
        return edit_comment_mutation(content, gql_client)
    else:
        print("action not exitsts")
        return False