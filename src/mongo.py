import pymongo
from src.gql import gql_query, gql_single_story
import os
import datetime

def connect_db(mongo_url: str, env: str='dev'):
    client = pymongo.MongoClient(mongo_url)
    db = None
    if env=='staging':
        db = client.staging
    elif env=='prod':
        db = client.prod
    else:
        db = client.dev
    return db

# create the story in Mongo if it doesn't exist
def create_story(db, gql_endpoint, story_id):    
    # check the story in mongodb
    col_stories = db.stories
    data = col_stories.find_one(story_id, {'url': 1})
    if data:
        return None
    
    # get data from postgres
    story, _ = gql_query(gql_endpoint, gql_single_story.format(ID=story_id))
    story = story['story']
    mongo_story_info = {
        '_id': story['id'],
        'url': story['url'],
        'publisher_id': story['source']['id'] if story['source'] else None, # publisher might be deleted
        'og_title': story['og_title'],
        'og_image': story['og_image'],
        'og_description': story['og_description'],
        'full_screen_ad': story['full_screen_ad'],
        'isMember': story['isMember'],
        # following fields are user action, we only store member_id which pick is active
        'reads': [],        # member_id list
        'comments': [],
    }
    result = col_stories.insert_one(mongo_story_info)
    if result:
        print(f'successfully insert {story_id}, inserted_id: {result.inserted_id}')
    return mongo_story_info

def add_read(db, member_id: str, story_id: str):    
    # check input
    gql_endpoint = os.environ['GQL_ENDPOINT']
    check_input = (member_id and story_id)
    if check_input==None:
        return False
    
    # connect db
    col_members, col_stories = db.members, db.stories
    
    # update member collection
    member_info = col_members.find_one(member_id, {"story_reads": 1})
    member_story_reads = member_info['story_reads']
    reads = set([read['sid'] for read in member_story_reads])
    if story_id in reads:
        print('The data has already existed')
        return False
    
    query  = {"_id": member_id}
    action = {"$push": {'story_reads': {
        "ts": int(datetime.datetime.now().timestamp()),
        "sid": story_id
    }}}
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_add_read: update member: {member_id}, append with read: {story_id}')

    # update story collection
    story_info = col_stories.find_one(story_id, {"reads": 1})
    if story_info==None:
        story_info = create_story(db, gql_endpoint, story_id) # create story before update
    query = {"_id": story_id}
    action = {"$push": {'reads': member_id}}
    result = col_stories.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_add_read: update story: {story_id}, add member_id: {member_id} read')
    return True

def remove_read(db, member_id: str, story_id: str):    
    # check input
    check_input = (member_id and story_id)
    if check_input==None:
        return False
    
    # connect db
    col_members, col_stories = db.members, db.stories
    
    # update member collection
    query  = {"_id": member_id}
    action = {
        "$pull": {
            "story_reads": {
                "sid": story_id
            }
        }
    }
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_read: remove member: {member_id} with read: {story_id}')

    # update story collection
    query = {"_id": story_id}
    action = {
        "$pull": {
            'reads': member_id
        }
    }
    result = col_stories.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_read: remove reads of story: {story_id} with member_id: {member_id}')
    return True 

### You need to call this function after you get comment_id which is id in postgresql
def add_comment(db, member_id: str, comment_id: str, story_id: str, content: str=''):    
    # check input
    gql_endpoint = os.environ['GQL_ENDPOINT']
    check_input = (member_id and comment_id and story_id and content)
    if check_input==None:
        return False
    
    # connect db
    col_members, col_stories = db.members, db.stories
    
    # update member collection
    query  = {"_id": member_id}
    action = {
        "$push": {
            'story_comments': {
                "ts": int(datetime.datetime.now().timestamp()),
                "cid": comment_id,
                "sid": story_id,
                "content": content,
            }
        }
    }
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_add_comment: update member: {member_id}, append comment_id: {comment_id}')

    # update story collection
    story = col_stories.find_one(story_id)
    if story==None:
        story = create_story(db, gql_endpoint, story_id)
    query  = {"_id": story_id}
    action = {
        "$push": {
            'comments': {
                "mid": member_id,
                "cid": comment_id,
            }
        }
    }
    result = col_stories.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_add_comment: update story: {story_id}, add comment_id: {comment_id}')
    return True 

def edit_comment(db, member_id: str, comment_id: str, new_content: str):
    # check input
    check_input = (member_id and comment_id and new_content)
    if check_input==None:
        return False
    
    # connect db
    col_members = db.members
    
    # $ is used to update the matched element
    result = col_members.update_one(
        {"_id": member_id, "story_comments.cid": comment_id},
        {"$set": {"story_comments.$.content": new_content}}
    )
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_edit_comment: update member: {member_id}, comment_id: {comment_id}')
    return True

def remove_comment(db, member_id:str, comment_id: str):    
    # check input
    check_input = (member_id and comment_id)
    if check_input==None:
        return False
    
    # connect db
    col_members, col_stories = db.members, db.stories

    # story_id should be inferred from member's data
    member_comments = col_members.find_one(member_id)['story_comments']
    target_story = None
    for comment in member_comments:
        if comment['cid'] == comment_id:
            target_story = comment['sid']
    if target_story==None:
        print('mongo_remove_comment: cannot find corresponding story_id when remove comment')
        return False
    
    # update member collection
    query  = {"_id": member_id}
    action = {
        "$pull": {
            "story_comments": {
                "cid": comment_id
            }
        }
    }
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_comment: remove member: {member_id} with comment_id: {comment_id}')

    # update story collection
    query = {"_id": target_story}
    action = {
        "$pull": {
            'comments': {
                "cid": comment_id
            }
        }
    }
    result = col_stories.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_comment: remove comment of story: {target_story} with comment_id: {comment_id}')
    return True

def add_follow(db, member_id: str, followed_member_id: str):
    # check input
    check_input = (member_id and followed_member_id)
    if check_input==None:
        return False
    
    # connect db
    col_members = db.members

    # get the information about two members
    members_info = list(col_members.find(
        {
            "_id": {
                "$in": [member_id, followed_member_id]
            }
        },
        {
            "following": 1,
            "follower": 1,
        }
    ))
    source_member_info, followed_member_info = None, None
    for member in members_info:
        if member['_id'] == member_id:
            source_member_info = member
        if member['_id'] == followed_member_id:
            followed_member_info = member
    if source_member_info==None or followed_member_info==None:
        print("cannot get information from either member_id or followed_member_id")
        return False

    # update source member
    # source
    source_member_following = set(source_member_info['following'])
    if followed_member_id not in source_member_following:
        result = col_members.update_one(
            {"_id": member_id},
            {"$push": {"following": followed_member_id}}
        )
        updateExisting = result.raw_result.get('updatedExisting', False)
        if updateExisting:
            print(f'mongo_add_follow: member {member_id} add following {followed_member_id}')
    # target
    followed_member_follower = set(followed_member_info['follower'])
    if member_id not in followed_member_follower:
        result = col_members.update_one(
            {"_id": followed_member_id},
            {"$push": {"follower": member_id}}
        )
        updateExisting = result.raw_result.get('updatedExisting', False)
        if updateExisting:
            print(f'mongo_add_follow: member {followed_member_id} add follower {member_id}')
    return True

def remove_follow(db, member_id:str, followed_member_id: str):    
    # check input
    check_input = (member_id and followed_member_id)
    if check_input==None:
        return False
    
    # connect db
    col_members = db.members
    
    # update source member
    query  = {"_id": member_id}
    action = {
        "$pull": {
            "following": followed_member_id
        }
    }
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_follow: remove member: {member_id} following: {followed_member_id}')

    # update target member
    query = {"_id": followed_member_id}
    action = {
        "$pull": {
            "follower": member_id
        }
    }
    result = col_members.update_one(query, action)
    updateExisting = result.raw_result.get('updatedExisting', False)
    if updateExisting:
        print(f'mongo_remove_follow: remove member {followed_member_id} follower: {member_id}')
    return True 