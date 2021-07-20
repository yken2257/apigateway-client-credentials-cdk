# Secure API Gateway with OAuth 2.0 Client Credentials grant
We are going to build a secure API gateway using AWS Cognito with OAuth 2.0 client credentials grant.
AWS CDK with Python is employed to build a CloudFormation stack.
This application architecture is composed of Amazon Cognito, Amazon API Gateway, and AWS Lambda.

![aws-config](https://user-images.githubusercontent.com/54834903/126245519-75d6d0d8-6ee3-4675-b43b-9daae0a57029.png)

## Prerequisites
- Python
    - pipenv
- AWS CLI
- AWS CDK
- jq (if necessary)
## Usage
### Set up
1. Clone this repository
    ```bash
   $ git clone git@github.com:yken2257/apigateway-client-credentials-cdk.git
   $ cd apigateway-client-credentials-cdk
   $ cp .env.example .env
    ```

 1. Edit `.env` as you like
    ```shell script:.env
    STACK_NAME=SecuredApiGatewayStack
    COGNITO_DOMAIN_PREFIX=sendgrid-event-webhook-test
    ```

 1. Install packages with pipenv
     ```bash
    $ pipenv install
    $ pipenv shell
    ```

 1. Load `.env` as bash variables
    ```bash
    $ export $(cat .env)
    ```

 1. Deploy stack
    ```bash
    $ cdk deploy
    ```

 1. Get User Pool ID and API endpoint URL
    If the stack is successfully deployed, the User Pool ID and the endpoint URL of API Gateway are displayed.
    ```
    Outputs:
    SecuredApiGatewayStack.CognitoUserPoolId = ap-northeast-1_xxxxxx
    SecuredApiGatewayStack.PrintPostStackApiEndpoint56282721 = https://yyyyyy.execute-api.ap-northeast-1.amazonaws.com/prod/
    ```

    Define them as bash variables:
    ```bash
    $ USER_POOL_ID=ap-northeast-1_xxxxxx
    $ ENDPOINT_URL=https://yyyyyy.execute-api.ap-northeast-1.amazonaws.com/prod/activity
    ```
    
    Note that the path `activity` has to be added to the endpoint url. 

    The User Pool ID and the URL can also be obtained with `aws cloudformation decribe-stacks` command:

    ```bash
    $ USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
      | jq -r '.Stacks[] | .Outputs[] | select(.OutputKey == "CognitoUserPoolId") | .OutputValue')
    $ ENDPOINT_URL=$(aws cloudformation describe-stacks \
      --stack-name $STACK_NAME \
      | jq -r '.Stacks[] | .Outputs[] | select(.ExportName == "PrintPostStackApi") | .OutputValue')'activity'
    ```

1. Create an app client and get its Client ID and Client Secret
    ```bash
    $ aws cognito-idp create-user-pool-client \
    --user-pool-id $USER_POOL_ID \
    --client-name "full-access-client" \
    --generate-secret \
    --allowed-o-auth-flows "client_credentials" \
    --allowed-o-auth-scopes "activity/*" \
    --allowed-o-auth-flows-user-pool-client

    {
        "UserPoolClient": {
            "UserPoolId": "ap-northeast-1_xxxxxxxxx",
            "ClientName": "full-access-client",
            "ClientId": "<<CLIENT_ID>>",
            "ClientSecret": "<<CLIENT_SECRET>>",
            "LastModifiedDate": "2021-06-30T08:48:07.793000+09:00",
            "CreationDate": "2021-06-30T08:48:07.793000+09:00",
            "RefreshTokenValidity": 30,
            "AllowedOAuthFlows": [
                "client_credentials"
            ],
            "AllowedOAuthScopes": [
                "activity/*"
            ],
            "AllowedOAuthFlowsUserPoolClient": true
        }
    }
    ```
    Memorize `<<CLIENT_ID>>` and `<<CLIENT_SECRET>>`.

    ```bash
    $ CLIENT_ID=<<CLIENT_ID>>
    $ CLIENT_SECRET=<<CLIENT_SECRET>>
    ```

### Test the configration

1. Request a token

    ```bash
    $ TOKEN_URL=https://${COGNITO_DOMAIN_PREFIX}.auth.<<AWS_REGION>>.amazoncognito.com/oauth2/token
    $ AUTH=$(echo -n "${CLIENT_ID}:${CLIENT_SECRET}" | base64)
    $ curl --url $TOKEN_URL \
    --header "Authorization: Basic $AUTH" \
    --header "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=client_credentials"

    {"access_token":"<<ACCESS_TOKEN>>","expires_in":3600,"token_type":"Bearer"}
    ```
    For the token endpoint, see [the official document](https://docs.aws.amazon.com/cognito/latest/developerguide/token-endpoint.html).

1. Access the API endpoint
    ```bash
    $ curl --url $ENDPOINT_URL \
    --header "Authorization: Bearer <<ACCESS_TOKEN>>" \
    --data '{"message":"Hello"}'

    {\"message\":\"Hello\"}
    ```

    The Lambda function just responses the request body, if successfully configured. The request body would also be shown on the Amazon CloudWatch Logs. 

## Apply to SendGrid Event Webhook

[SendGrid](https://sendgrid.com) provides "Event Webhook", which POSTs the sending logs to your server. 
This has an option that enables you to secure your server with OAuth 2.0 Client Credentials grant. Test the configration of our API gateway with this feature. 
SendGrid POSTs JSON data when the token endpoint, client id, client secret, and the API endpoint are correctly configured. This can be tested via SendGrid's API:

```bash
$ curl --url https://api.sendgrid.com/v3/user/webhooks/event/test \
--header "Content-Type: application/json" \
--header "Authorization: Bearer $SENDGRID_API_KEY" \
--data '{"url": "'$ENDPOINT_URL'", 
"oauth_client_id": "'$CLIENT_ID'",
"oauth_client_secret": "'$CLIENT_SECRET'", 
"oauth_token_url": "'$TOKEN_URL'"}'
```
When the API is successfully called, check if the JSON data are POSTed on Amazon CloudWatch Logs.
See [the official docment](https://docs.sendgrid.com/api-reference/webhooks/test-event-notification-settings) for the SendGrid API.
