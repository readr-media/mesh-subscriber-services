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
    }}
}}
'''