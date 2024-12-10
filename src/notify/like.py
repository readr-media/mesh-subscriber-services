import src.config as config
from src.tool import get_current_timestamp, gen_uuid
from src.gql import gql_query
from src.notify.aggregate import aggregate_notify
from src.notify.content import get_objective_content

gql_comment_creator = '''
query Comment{{
  comment(where: {{id: {ID} }}){{
    member{{
        id
        is_active
    }}
    story{{
        id
    }}
  }}
}}
'''

def notify_add_like(db, data, aggregate: bool=True):
    '''
        Case: 使用者[Member_name]喜歡你的留言[Comment_content]
    '''
    memberId = data.get('memberId', config.INVALID_ID)
    commentId = data.get('commentId', config.INVALID_ID)
    if memberId==config.INVALID_ID or commentId==config.INVALID_ID:
        return False
    new_notify = {
        "uuid": gen_uuid(),
        "read": False,
        "action": "add_like",
        "objective": "comment", # add_pick's objective is "comment" only
        "targetId": commentId,
        "aggregate": aggregate,
        "from": [memberId],
        "ts": get_current_timestamp()
    }
    content = get_objective_content("comment", commentId)
    if content:
        new_notify['content'] = content

    comment, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_comment_creator.format(ID=commentId))
    if error_msg:
        return False
    creator = comment['comment']['member'] 
    if creator.get('is_active', False)==False:
        return False
    creatorId = creator['id']
    if creatorId!=memberId:
        aggregate_notify(db, memberId, creatorId, new_notify)
        print(f"add_like: notify recipientId {creatorId}")
    return True