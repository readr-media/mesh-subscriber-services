from src.gql import gql_collection_member, gql_comment_member, gql_query
import os
from gql import gql


def report_handler(content, gql_client):
    memberId = content['memberId'] if 'memberId' in content and content['memberId'] else False
    targetId = content['targetId'] if 'targetId' in content and content['targetId'] else False
    obj = content['objective'] if 'objective' in content and content['objective'] else False
    reasonId = content['reasonId'] if 'reasonId' in content and content['reasonId'] else False
    if not (memberId or targetId or obj or reasonId) or 'comment' not in content:
        print("no required data for action")
        return False

    report_gql = None
    gql_endpoint = os.environ['GQL_ENDPOINT']
    respondentId = None
    if obj == 'comment':
        report_gql = gql_comment_member
        respondentId, _ = gql_query(gql_endpoint, report_gql.format(ID=targetId))
        respondentId = respondentId['comment']['member']['id']
    else:
        report_gql = gql_collection_member
        respondentId, _ = gql_query(gql_endpoint, report_gql.format(ID=targetId))
        respondentId = respondentId['collection']['creator']['id']
    
    action = content['action']
    if action == 'add_report_record':
        try:
            fields = [
                f"informant:{{connect:{{id:{memberId}}}}}",
                f"reason:{{connect:{{id:{reasonId}}}}}",
                f"respondent:{{connect:{{id:{respondentId}}}}}",
            ]
            if obj == 'comment':
                fields.append(f"comment:{{connect:{{id:{targetId}}}}}")
            else:
                fields.append(f"collection:{{connect:{{id:{targetId}}}}}")

            fields_string = ", ".join(fields)

            mutation = f'''
                mutation {{
                    createReportRecord(data:{{
                        {fields_string}
                    }})
                    {{
                        id
                    }}
                }}
            '''
            result = gql_client.execute(gql(mutation))
            return True if isinstance(result, dict) and 'createReportRecord' in result else False
        except Exception as e:
            print(f"add_report failed: {str(e)}")
    return False



