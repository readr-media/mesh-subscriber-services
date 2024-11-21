import os

TIME_ZONE = "Asia/Taipei"
CUSTOME_MEMBER = -1
INVALID_ID = -1
MEILISEARCH_COLLECTION_INDEX = 'mesh_collection'
MEILISEARCH_MEMBER_INDEX = 'mesh_member'
MONGO_NOTIFY_COLLECTION = 'notifications'
NOTIFY_UUID_LENGTH = 8
MOST_NOTIFY_RECORDS = 200
MESH_GQL_ENDPOINT = os.environ.get('GQL_ENDPOINT', '')

### First layer is action, second layer is objectives
# If the objectives list is "None", it means the pubsub has no objective field.
VALID_NOTIFY_ACTIONS = {
    "add_follow": ["member"],
    "add_comment": ["story", "comment", "collection"],
    "add_pick": ["collection"],
    "add_like": ["None"],
    "add_pick_and_comment": ["story", "collection"],
    "add_collection": ["None"]
}