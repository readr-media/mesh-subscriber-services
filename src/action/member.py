from src.mongo import connect_db, syncMember, updateMemberActive
import os
from src.gql import gql_single_member, gql_update_member, gql_update_comments, gql_update_invitationCodes, gql_update_picks
from gql import gql

def member_handler(content, gql_client):
    action = content['action']
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    if int(memberId) < 0:
        print("member is visitor")
        return True
    if not(memberId):
        print("no required data for action")
        return False
    try:
        mongo_url = os.environ.get('MONGO_URL', None)
        env = os.environ.get('ENV', 'dev')
        db = connect_db(mongo_url, env)
        if action == "update_member":
            member = gql_client.execute(gql(gql_single_member.format(ID=memberId)))
            member = member['member']
            if member:
                syncMember(db, member)
        if action == "remove_member":
            state = content.get('state', False)
            result = deactivate_member_actions(gql_client, memberId, state)
            if result:
                print("Deactivate member data in CMS successed")
            result = updateMemberActive(db, member_id=memberId, state=state)
            if result:
                print("Deactivate member data in MongoDB successed")
    except Exception as e:
        print(str(e))
    return True

def deactivate_member_actions(gql_client, member_id, state=False):
    try:
        # update member
        update_member_var = {
            "where": {
                "id": member_id
            },
            "data": {
                "is_active": state
            }
        }
        member = gql_client.execute(gql(gql_update_member), variable_values=update_member_var)
        if "updateMember" in member:
            print(f"Deactivate member {member_id} is_active successed")
        member = member['updateMember']
        
        # update picks
        picks = member['pick']
        if len(picks)>0:
            pick_variable = {
                "data": [{"where": {"id": pick['id']}, "data": {"is_active": state}} for pick in picks]
            }
            data = gql_client.execute(gql(gql_update_picks), variable_values=pick_variable)
            if "updatePicks" in data:
                print(f"Deactivate member {member_id} picks successed")
        else:
            print(f"No need to deactivate member {member_id} picks")
        
        # update comments
        comments = member['comment']
        if len(comments)>0:
            comment_variable = {
                "data": [{"where": {"id": comment['id']}, "data": {"is_active": state}} for comment in comments]
            }
            data = gql_client.execute(gql(gql_update_comments), variable_values=comment_variable)
            if "updateComments" in data:
                print(f"Deactivate member {member_id} comments successed")
        else:
            print(f"No need to deactivate member {member_id} comments")

        # update invitations, only when state==False and set all expired
        codes = member['invited']
        if len(codes)>0 and state==False:
            code_variable = {
                "data": [{"where": {"id": code['id']}, "data": {"expired": True}} for code in codes]
            }
            data = gql_client.execute(gql(gql_update_invitationCodes), variable_values=code_variable)
            if "updateInvitationCodes" in data:
                print(f"Deactivate member {member_id} invitationCodes successed")
        else:
            print(f"No need to deactivate member {member_id} invitationCodes")
    except Exception as e:
        print(f"Update member {member_id} with some error: ", e)
        return False
    return True