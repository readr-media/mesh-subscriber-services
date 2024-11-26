import src.config as config
from src.tool import get_current_timestamp, gen_uuid
from src.gql import gql_query

gql_member_followers = '''
query Member{{
  member(where: {{id: {ID} }}){{
    follower{{
      id
      is_active
    }}
  }}
}}
'''

def notify_add_collection(db, data):
    '''
        Case: 用戶[MemberId]建立了新的集錦[Collection_title]
    '''
    memberId = data.get('memberId', config.INVALID_ID)
    collectionId = data.get('collectionId', config.INVALID_ID)
    if memberId==config.INVALID_ID or collectionId==config.INVALID_ID:
        return False
    new_notify = {
        "uuid": gen_uuid(),
        "read": False,
        "action": "add_collection",
        "objective": "collection",
        "targetId": collectionId,
        "aggregate": False,
        "from": memberId,
        "ts": get_current_timestamp()
    }

    # get recipients
    recipients = []
    member, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_member_followers.format(ID=memberId))
    if error_msg:
        return False
    followers = member['member']['follower']
    for follower in followers:
        is_active = follower['is_active']
        if is_active==True:
            recipients.append(follower['id'])

    # send notifies
    col_notifies = db.notifications
    for recipientId in recipients:
        if recipientId==memberId:
            continue
        notifier = col_notifies.find_one(recipientId)
        if notifier==None:
            notifier = {
                "_id": recipientId,
                "lrt": 0,
                "notifies": [new_notify]
            }
            col_notifies.insert_one(notifier)
        else:
            new_notifies = notifier['notifies']
            new_notifies.insert(0, new_notify)
            new_notifies = new_notifies[:config.MOST_NOTIFY_RECORDS]
            col_notifies.update_one(
                {"_id": recipientId},
                {"$set": {"notifies": new_notifies}}
            )
        print(f"add_collection: notify recipient {recipientId}")
    return True