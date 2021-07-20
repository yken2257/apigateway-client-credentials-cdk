import json

def handler(event, content):
    try:
        body = event.get("body")
        print(body)
        status_code = 200
    except Exception as e:
        status_code = 500
        body = {"description": str(e)}
    return {
        "statusCode": status_code,
        "headers": {
            "Content-Type": "application/json"
        },
        "body": json.dumps(body)
    }