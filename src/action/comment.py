import datetime
from gql import gql
import os
from src.mongo import connect_db, add_comment, remove_comment, edit_comment

def add_comment_mutation(content, gql_client):
    memberId = content.get('memberId', -1)
    if memberId=='customId' or int(memberId) < 0:
        print("member is not valid to add comment")
        return True
    
    targetId = content.get('targetId', False)
    state = content.get('state', False)
    comment_content = content.get('content', False)
    comment_content = str(comment_content).replace("\n", "\\n") if comment_content else False
    obj = content.get('objective', False)
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
        # synchronize mongodb
        try:
            commentId = result['createComment']['id']
            mongo_url = os.environ.get('MONGO_URL', None)
            env = os.environ.get('ENV', 'dev')
            if obj=='story' and targetId:
                db = connect_db(mongo_url, env)
                add_comment(db, memberId, commentId, targetId, comment_content)
        except Exception as e:
            print(f"mongo add_comment failed: {str(e)}")
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
                    member{
                        id
                    }
                }
            }''' % (commentId)
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'updateComment' in result:
        # synchronize mongodb
        try:
            memberId  = result['updateComment']['member']['id']
            commentId = result['updateComment']['id']
            mongo_url = os.environ.get('MONGO_URL', None)
            env = os.environ.get('ENV', 'dev')
            if commentId:
                db = connect_db(mongo_url, env)
                remove_comment(db, memberId, commentId)
        except Exception as e:
            print(f"mongo remove_comment failed: {str(e)}")
        return True
    return False

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
                    member{
                        id
                    }
                }
            }''' % (commentId, comment_content)
    result = gql_client.execute(gql(mutation))
    if isinstance(result, dict) and 'updateComment' in result:
        # synchronize mongodb
        try:
            memberId  = result['updateComment']['member']['id']
            commentId = result['updateComment']['id']
            mongo_url = os.environ.get('MONGO_URL', None)
            env = os.environ.get('ENV', 'dev')
            if commentId:
                db = connect_db(mongo_url, env)
                edit_comment(db, memberId, commentId, comment_content)
        except Exception as e:
            print(f"mongo edit_comment failed: {str(e)}")
        return True
    return False

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