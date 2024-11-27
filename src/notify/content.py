from src.gql import gql_query
from src.config import MESH_GQL_ENDPOINT

gql_notify_member = '''
query Member{{
  member(where: {{id: {ID} }}){{
    id
    customId
    name
    avatar
  }}
}}
'''

gql_notify_story = '''
query Story{{
  story(where: {{id: {ID} }}){{
    id
    title
    url
    source{{
      id
      customId
      title
    }}
    commentCount(where: {{is_active: {{equals: true}} }})
  }}
}}
'''

gql_notify_comment = '''
query Comment{{
  comment(where: {{id: {ID} }}){{
    id
    content
  }}
}}
'''

gql_notify_collection = '''
query Collection{{
  collection(where: {{id: {ID} }}){{
    id
    title
  }}
}}
'''

def get_objective_content(objective, targetId):
    content = None
    try:
        if objective=="story":
            gql_string = gql_notify_story.format(ID=targetId)
            data = gql_query(MESH_GQL_ENDPOINT, gql_string)
            content = data['story']
        if objective=="comment":
            gql_string = gql_notify_comment.format(ID=targetId)
            data = gql_query(MESH_GQL_ENDPOINT, gql_string)
            content = data['comment']        
        if objective=="collection":
            gql_string = gql_notify_collection.format(ID=targetId)
            data = gql_query(MESH_GQL_ENDPOINT, gql_string)
            content = data['collection']
    except:
        print(f"get_objective_content error: cannot find {objective} {targetId}")
    return content