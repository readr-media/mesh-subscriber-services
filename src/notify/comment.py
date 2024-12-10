import src.config as config
from src.tool import get_current_timestamp, gen_uuid
from src.gql import gql_query
from src.notify.aggregate import aggregate_notify
from src.notify.content import get_objective_content

gql_story_comment = '''
query Story{{
  story(where: {{id: {ID} }}){{
    comment{{
      member{{
        id
        is_active
      }}
    }}
  }}
}}
'''

gql_collection_comment = '''
query Collection{{
  collection(where: {{id: {ID} }}){{
    comment{{
      member{{
        id
        is_active
      }}
    }}
    creator{{
        id
        is_active
    }}
  }}
}}
'''

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

def notify_add_comment(db, data):
    '''
        Case1: add_comment_story, 用戶[MemberId]也在文章[StoryId]底下留言
        Case2: add_comment_collection, 用戶[MemberId]在你的集錦[CollectionId]底下留言
        Case3: add_comment_comment, 用戶[MemberId]回覆了你的留言[CommentId]
    '''
    objective = data.get('objective', None)
    memberId = data.get('memberId', config.INVALID_ID)
    state = data.get('state', "public")
    if objective==None or memberId==config.INVALID_ID or state!="public":
        return False
    
    # Case1: add_comment_story
    if objective=='story':
        storyId = data['targetId']
        story, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_story_comment.format(ID=storyId))
        if error_msg:
            return False
        members = story['story']['comment']
        
        ### get recipients
        recipients = []
        for memberInfo in members:
            member = memberInfo['member']
            if member.get('is_active', False)==False:
                continue
            recipients.append(member['id'])
        recipients = set(recipients)   # prevent multiple notifications to same member
        recipients.discard(memberId)    # prevent notify notifier
        recipients = list(recipients) 
        
        ### add new notify into document
        new_notify = {
            "uuid": gen_uuid(),
            "read": False,
            "action": "add_comment",
            "objective": "story",
            "targetId": storyId,
            "aggregate": True,
            "from": [memberId],
            "ts": get_current_timestamp(),
        }
        content = get_objective_content("story", storyId)
        if content:
            new_notify['content'] = content
        for recipientId in recipients:
            print(f"add_comment_story: notify recipientId {recipientId}")
            aggregate_notify(db, memberId, recipientId, new_notify)
        
    # Case2: add_comment_collection
    if objective=='collection':
        collectionId = data['targetId']
        collection, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_collection_comment.format(ID=collectionId))
        if error_msg:
            return False
        members = collection['collection']['comment']
        creator = collection['collection']['creator']
        
        ### get recipients, contains commented member and collection creator
        recipients = []
        for memberInfo in members:
            member = memberInfo['member']
            if member.get('is_active', False)==False:
                continue
            recipients.append(member['id'])
        if creator.get('is_active', False)==True:
            recipients.append(creator['id'])
        recipients = set(recipients)   # prevent multiple notifications to same member
        recipients.discard(memberId)    # prevent notify notifier
        recipients = list(recipients) 

        ### add new notify into document
        new_notify = {
            "uuid": gen_uuid(),
            "read": False,
            "action": "add_comment",
            "objective": "collection",
            "targetId": collectionId,
            "aggregate": True,
            "from": [memberId],
            "ts": get_current_timestamp(),
        }
        content = get_objective_content("collection", collectionId)
        if content:
            new_notify['content'] = content
        
        for recipientId in recipients:
            print(f"add_comment_collection: notify recipientId {recipientId}")
            aggregate_notify(db, memberId, recipientId, new_notify)
    
    # Case3: add_comment_comment
    if objective=='comment':
        commentId = data['targetId']
        comment, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_comment_creator.format(ID=commentId))
        if error_msg:
            return False
        creator = comment['comment']['member']
        
        # add_comment_comment has only one recipient
        recipientId = creator['id']
        if recipientId!=memberId:
            new_notify = {
                "uuid": gen_uuid(),
                "read": False,
                "action": "add_comment",
                "objective": "comment",
                "targetId": commentId,
                "aggregate": True,
                "from": [memberId],
                "ts": get_current_timestamp()
            }
            content = get_objective_content("comment", commentId)
            if content:
                new_notify['content'] = content
            print(f"add_comment_comment: notify recipientId {recipientId}")
            aggregate_notify(db, memberId, recipientId, new_notify)
    return True