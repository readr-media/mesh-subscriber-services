import src.config as config
from src.tool import get_current_timestamp, gen_uuid

def notify_add_follow(db, data):
    '''
        Case: 用戶[MemberId]已經開始追蹤你[targetId]
    '''
    memberId = data.get('memberId', config.INVALID_ID)
    targetId = data.get('targetId', config.INVALID_ID)
    if memberId==config.INVALID_ID or targetId==config.INVALID_ID:
        return False
    new_record = {
        "uuid": gen_uuid(),
        "read": False,
        "action": "add_follow",
        "objective": "member",
        "targetId": targetId,
        "aggregate": False,
        "from": memberId,
        "ts": get_current_timestamp()
    }

    col_records = db.notifications
    record = col_records.find_one(targetId)
    if record==None:
        record = {
            "_id": targetId,
            "lrt": 0,
            "notifies": [new_record]
        }
        col_records.insert_one(record)
    else:
        new_notifies = record['notifies']
        new_notifies.insert(0, new_record)
        new_notifies[:config.MOST_NOTIFY_RECORDS]
        col_records.update_one(
            {"_id": targetId},
            {"$set": {"notifies": new_notifies}}
        )
    print(f"add_follow: notify recipientId {targetId}")
    return True