from gql import gql

def filter_categories(action, memberId, categoryIds, gql_client):
    query = '''
        query{
            member(
                where: {
                    id: %s
                }
            ){
                following_category{
                    id
                }
            }
        }
    ''' % (memberId)
    response = gql_client.execute(gql(query))
    response_categories = response.get('member', {}).get('following_category', [])
    categories = [category.get('id') for category in response_categories]
    
    filtered_categories = []
    if action == 'connect':
        filtered_categories = [category for category in categoryIds if (category not in categories)]
    else:
        filtered_categories = [category for category in categories if (category in categoryIds)]
    return filtered_categories

def category_handler(content, gql_client):
    memberId = content.get('memberId', False)
    if int(memberId) < 0:
        print("member is visitor")
        return True
    
    categoryIds = content.get('categoryIds', False)
    if not(memberId and categoryIds):
        print("no required data for action")
        return False

    if content['action'] == 'add_category':
        action = 'connect'
    elif content['action'] == 'remove_category':
        action = 'disconnect'
    else:
        print("action not exitsts")
        return False
    
    ### check exists
    filtered_categories = filter_categories(action, memberId, categoryIds, gql_client)
    if len(filtered_categories)==0:
        print(f"no categories need to update for member {memberId}")
        return True
    
    gql_string = '''
        mutation ($data: MemberUpdateInput!, $id: ID!){
            updateMember(where: {id: $id}, data: $data) {
                following_category{
                    id
                }
                following_category_count
            }
        }
    '''
    gql_variable = {
        'id': memberId,
        'data': {
            'following_category': {
                action: [{'id': id} for id in categoryIds]
            }
        }
    }
    result = gql_client.execute(gql(gql_string), variable_values=gql_variable)
    return True if isinstance(result, dict) and 'updateMember' in result  else False