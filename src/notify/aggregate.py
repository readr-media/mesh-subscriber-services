import src.config as config
import copy
from src.tool import get_current_timestamp
NO_TARGET_IDX = -1

def aggregate_notify(db, notifierId: str, recipientId: str, new_notify: dict):
    aggregate = new_notify.get('aggregate', False)
    if aggregate==False:
        return False
    
    col_records = db.notifications
    record = col_records.find_one(recipientId)

    # Create recipient record if haven't created
    if record==None:
        record = {
            "_id": recipientId,
            "lrt": 0,
            "notifies": []
        }
        col_records.insert_one(record)
        print("Create new record for recipientId: ", recipientId)
    
    # Add notify
    all_notifies = record.get("notifies", [])
    target_idx = NO_TARGET_IDX
    for idx, notify in enumerate(all_notifies):
        action    = notify['action']
        objective = notify.get('objective', None)
        targetId  = notify.get('targetId', None)
        aggregate = notify.get('aggregate', False)
        if new_notify['action']==action and new_notify['targetId']==targetId and new_notify.get('objective', None)==objective and aggregate==True:
                target_idx = idx
                break
    if target_idx!=NO_TARGET_IDX:
        target_notify = copy.deepcopy(all_notifies[target_idx])
        target_notify['read'] = False
        target_notify['from'].insert(0, notifierId)
        target_notify['ts'] = get_current_timestamp()
        
        content = new_notify.get('content', None)
        if content:
            target_notify['content'] = content

        new_notifies = [target_notify] + all_notifies[:target_idx] + all_notifies[target_idx+1:]
        new_notifies = new_notifies[:config.MOST_NOTIFY_RECORDS]
        col_records.update_one(
            {"_id": recipientId},
            {"$set": {"notifies": new_notifies}}
        )
    else:
        new_notifies = [new_notify] + all_notifies
        new_notifies = new_notifies[:config.MOST_NOTIFY_RECORDS]
        col_records.update_one(
            {"_id": recipientId},
            {"$set": {"notifies": new_notifies}}
        )
    return True