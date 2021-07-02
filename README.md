# Secure API Gateway with OAuth2 Client Credentials grant
We are going to build a secure API gateway using AWS Cognito with OAuth 2.0 client credentials grant.
AWS CDK with Python is employed to build a CloudFormation stack.
This application architecture is composed of Amazon Cognito, Amazon API Gateway, and AWS Lambda.

## Prerequisites
- Python
    - pipenv
- AWS CLI
- AWS CDK
- jq
## Usage
### Set up
1. Clone this repository
    
    ```shell script
   $ git clone git@github.com:yken2257/
   $ cd
   $ cp .env.example .env
    ```
 1. Edit .env
 
    ```shell script:.env
    STACK_NAME=SecuredApiGatewayStack
    COGNITO_DOMAIN_PREFIX=sendgrid-event-webhook-test
    ```
 
 1. Install packages with pipenv
 
     ```shell script
    $ pipenv install
    $ pipenv shell
    ```
 
 1. Deploy stack
    ```shell script
    $ cdk deploy
    ```
 
 1. Load .env
 
    ```shell script
    $ export $(cat .env)
    ```
 
 1. Get the User Pool ID
 
    ```shell script
    $ USER_POOL_ID=$(aws cloudformation describe-stacks \
    --stack-name $STACK_NAME \
      | jq -r '.Stacks[] | .Outputs[] | select(.OutputKey == "CognitoUserPoolId") | .OutputValue' \
    )
    ```

1. Create an app client and get its Client ID and Client Secret

    ```shell script
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


### Test the configration

1. Request a token

    ```bash
    $ TOKEN_URL=https://${COGNITO_DOMAIN_PREFIX}.auth.<<AWS_REGION>>.amazoncognito.com/oauth2/token
    $ AUTH=$(echo -n "<<CLIENT_ID>>:<<CLIENT_SECRET>>" | base64)
    $ curl --request POST \
    --url ${TOKEN_URL} \
    --header "Authorization: Basic ${AUTH}" \
    --header "Content-Type: application/x-www-form-urlencoded" \
    --data-urlencode "grant_type=client_credentials"

    {"access_token":"<<ACCESS_TOKEN>>","expires_in":3600,"token_type":"Bearer"}
    ```
    For the token endpoint, see [the official document](https://docs.aws.amazon.com/ja_jp/cognito/latest/developerguide/token-endpoint.html).

1. Access the API endpoint
    ```shell script
    $ curl --request POST \
    --url https://xxx.execute-api.ap-northeast-1.amazonaws.com/prod/activity \
    --header "Authorization: Bearer <<ACCESS_TOKEN>>" \
    --data "Hello"

    Hello
    ```
    The Lambda function just responses the request body. 
    
    The endpoint URL can be obtained as follows, if you don't remember it:
    ```shell script
    $ ENDPOINT_URL=$(aws cloudformation describe-stacks \
      --stack-name CognitoClientCredentialsByCdkStack \
      | jq -r '.Stacks[] | .Outputs[] | select(.OutputName == "PrintPostStackApi") | .OutputValue' \
      ) 
    ```
### Apply to SendGrid Event Webhook

```shell script
$ curl --request POST \ 
--url https://api.sendgrid.com/v3/user/webhooks/event/test \
--header 'Authorization: Bearer <<SENDGRID_API_KEY>>' \
--data '{"url": "https://xxx.execute-api.ap-northeast-1.amazonaws.com/prod/activity", 
"oauth_client_id": "<<CLIENT_ID>>",
"oauth_client_secret": "<<CLIENT_SECRET>>", 
"oauth_token_url": "'$TOKEN_URL'"}'
```
https://docs.sendgrid.com/api-reference/webhooks/test-event-notification-settings
