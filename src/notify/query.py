from gql import gql

def picker(gql_client, list_name, targetId):
    membersId = []
    picker_script = '''
    query{
        picks(where:{%s:{id:{equals:"%s"}}, kind:{equals:"read"}, is_active:{equals:true}}){
            member{
                id
            }
        }
    }
    '''% (list_name, targetId)
    result = gql_client.execute(gql(picker_script))
    if isinstance(result,dict) and 'picks' in result:
        if isinstance(result['picks'],list):
            picks = result['picks']
            if picks:
                for pick in picks:
                    if 'member' in pick and pick['member']:
                        membersId.append(pick['member']['id'])
                    else:
                        print(f"query error in {list_name}_picker")
                        return False
            else:
                print("no pick exists.")# it will return empty list           
            return membersId
    print(f"query error in {list_name}_picker.")
    return False

def commenter(gql_client, list_name, targetId):
    membersId = []
    picker_script = '''
    query{
            comments(where:{%s:{id:{equals:"%s"}}, is_active:{equals:true}}){
            member{
                id
                }
            }
    }'''% (list_name, targetId)
    result = gql_client.execute(gql(picker_script))
    if isinstance(result,dict) and 'comments' in result:
        if isinstance(result['comments'],list):
            comments = result['comments']
            if comments:
                for comment in comments:
                    if 'member' in comment and comment['member']:
                        membersId.append(comment['member']['id'])
                    else:
                        print(f"query error in {list_name}_comments")
                        return False
            else:
                print("no comment exists.")# it will return empty list           
            return membersId
    print(f"query error in {list_name}_commenter.")
    return False


def creator(gql_client, list_name, creator_field_name, targetId):
    creator_script = '''
    query{
            %s(where:{id:"%s"}){
                %s{
                    id
                }
            }
        }
    '''%(list_name, targetId, creator_field_name)
    result = gql_client.execute(gql(creator_script))
    if isinstance(result,dict) and list_name in result :
        if isinstance(result[list_name],dict) and creator_field_name in result[list_name]:
            creator = result[list_name][creator_field_name]
            if creator:
                return [creator['id']]
    print(f"query error in {list_name}_creator.")
    return False
