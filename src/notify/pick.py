import src.config as config
from src.tool import get_current_timestamp, gen_uuid
from src.gql import gql_query
from src.notify.aggregate import aggregate_notify

gql_collection_pick = '''
query Collection{{
  collection(where: {{id: {ID} }}){{
    creator{{
        id
        is_active
    }}
  }}
}}
'''

def notify_add_pick(db, data, aggregate: bool=True):
    '''
        Case: 訊息: [Member_name]精選了你的集錦[Collection_title]
    '''
    memberId = data.get('memberId', config.INVALID_ID)
    targetId = data.get('targetId', config.INVALID_ID)
    objective = data.get('objective', None)
    if memberId==config.INVALID_ID or targetId==config.INVALID_ID or objective==None:
        return False
    new_notify = {
        "uuid": gen_uuid(),
        "read": False,
        "action": "add_pick",
        "objective": objective,
        "targetId": targetId,
        "aggregate": aggregate,
        "from": [memberId],
        "ts": get_current_timestamp()
    }

    if objective=="collection":
        collection, error_msg = gql_query(config.MESH_GQL_ENDPOINT, gql_collection_pick.format(ID=targetId))
        if error_msg:
            return False
        creator = collection['collection']['creator'] 
        if creator.get('is_active', False)==False:
            return False
        creatorId = creator['id']
        if creatorId!=memberId:
            aggregate_notify(db, memberId, creatorId, new_notify)
            print(f"add_pick: notify recipientId {creatorId}")
    # TODO: If need other objective notification, you should implement them 
    return True