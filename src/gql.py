from gql.transport.requests import RequestsHTTPTransport
from gql import gql, Client

def gql_query(gql_endpoint, gql_string: str=None, gql_variables: str=None):
    '''
        gql_fetch is used to retrieve data
    '''
    json_data, error_message = None, None
    try:
      gql_transport = RequestsHTTPTransport(url=gql_endpoint)
      gql_client = Client(transport=gql_transport,
                          fetch_schema_from_transport=True)
      if gql_variables:
        json_data = gql_client.execute(gql(gql_string), variable_values=gql_variables)
      else:
        json_data = gql_client.execute(gql(gql_string))
    except Exception as e:
      print("GQL query error:", e)
      error_message = e
    return json_data, error_message

### Predefined gql queries
gql_stories = """
query Stories{{
  stories(where: {{source: {{id: {{equals: {ID} }} }} }}, take: {TAKE}, orderBy: {{published_date: desc}} ){{
    id
    title
    source{{
      id
      title
    }}
    url
    summary
    content
  }}
}}
"""

### 查詢某篇文章的內容
gql_single_story = '''
query Story{{
    story(where: {{id: {ID} }}){{
        id
        url
        source{{
          id
        }}
        og_title
        og_image
        og_description
        full_screen_ad
        isMember
        published_date
    }}
}}
'''

### 查詢單一member
gql_single_member = '''
query Member{{
  member(where: {{id: {ID} }}){{
    id
    customId
    name
    is_active
    nickname
    avatar
    following{{
      id
    }}
    follower{{
      id
    }}
    reads: pick(where: {{
      objective: {{
        equals: "story"
      }},
      kind: {{
        equals: "read"
      }},
      is_active: {{
        equals: true
      }}
    }}){{
      createdAt
      story{{
        id
      }}
    }}
    comments: comment(
      where: {{
        is_active: {{
          equals: true
        }},
        story: {{
          NOT: {{}}
        }}
      }}
    ){{
        createdAt
        content
        story{{
            id
        }}
    }}
  }}
}}
'''

### For remove member pubsub
gql_update_member = '''
mutation updateMember($where: MemberWhereUniqueInput!, $data: MemberUpdateInput!){
  updateMember(where: $where, data: $data){
    id
    is_active
    pick{
      id
    }
    comment{
      id
    }
    invited{
      id
    }
  }
}
'''

gql_update_picks = '''
mutation updatePicks($data: [PickUpdateArgs!]!){
    updatePicks(data: $data){
        id
        is_active
    }
}
'''

gql_update_comments = '''
mutation updateComments($data: [CommentUpdateArgs!]!){
    updateComments(data: $data){
        id
        is_active
    }
}
'''

gql_update_invitationCodes = '''
mutation updateInvitationCodes($data: [InvitationCodeUpdateArgs!]!){
  updateInvitationCodes(data: $data){
    id
    expired
  }
}
'''

### 查詢該集錦屬於哪個用戶
gql_collection_member = '''
query Collection{{
    collection(where: {{id: {ID} }}){{
        creator {{
            id
            name
        }}
    }}
}}
'''

### 查詢該留言屬於哪個用戶
gql_comment_member = '''
query Comment{{
    comment(where: {{id: {ID} }}){{
        member {{
            id
            name
        }}
        content
    }}
}}
'''