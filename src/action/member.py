from src.mongo import connect_db, syncMember
import os
from src.gql import gql_single_member
from gql import gql

def member_handler(content, gql_client):
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    if not(memberId):
        print("no required data for action")
        return False
    try:
        member = gql_client.execute(gql(gql_single_member.format(ID=memberId)))
        member = member['member']
        if member:
            mongo_url = os.environ.get('MONGO_URL', None)
            env = os.environ.get('ENV', 'dev')
            db = connect_db(mongo_url, env)
            syncMember(db, member)
    except Exception as e:
        print(str(e))
    return True
    
    