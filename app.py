import os
from aws_cdk import (
    core,
    aws_lambda as _lambda,
    aws_apigateway as apigw,
    aws_cognito as cognito
)

stack_name = os.environ.get('STACK_NAME')
domain_prefix = os.environ.get('COGNITO_DOMAIN_PREFIX')

class PrintPostStack(core.Stack):

    def __init__(self, scope: core.App, name: str, **kwargs) -> None:
        super().__init__(scope, name, **kwargs)

        user_pool = cognito.UserPool(
            self, 'UserPool',
            user_pool_name='EventWebhookUserPool'
        )

        scope_name = '*'
        full_access_scope = cognito.ResourceServerScope(
            scope_name=scope_name,
            scope_description='Full access'
        )

        resource_path = 'activity'
        user_pool.add_resource_server(
            'ResourceServer',
            identifier=resource_path,
            scopes=[full_access_scope]
        )

        # Specify an unique domain for the token endpoint
        cognito_domain = cognito.CognitoDomainOptions(
            domain_prefix=domain_prefix
        )

        user_pool.add_domain(
            'EventWebhookCognitoDomain',
            cognito_domain=cognito_domain
        )

        # Write out the value of user_pool_id returned by the aws cloudformation describe-stacks command
        core.CfnOutput(self, 'CognitoUserPoolId',
                       value=user_pool.user_pool_id)

        lambda_func = _lambda.Function(
            self, "PrintPostFunc",
            code=_lambda.Code.from_asset('lambda'),
            handler="webhook.handler",
            runtime=_lambda.Runtime.PYTHON_3_8,
        )

        api = apigw.RestApi(self, "PrintPostStackApi",
                            endpoint_export_name="PrintPostStackApi")

        authorizer = apigw.CfnAuthorizer(
            self, 'APIGatewayAuthorizer',
            identity_source='method.request.header.Authorization',
            provider_arns=[user_pool.user_pool_arn],
            rest_api_id=api.rest_api_id,
            type='COGNITO_USER_POOLS',
            name='my_authorizer'
        )

        resource = api.root.add_resource(resource_path)
        method = resource.add_method(
            'POST',
            apigw.LambdaIntegration(lambda_func),
            authorization_type=apigw.AuthorizationType.COGNITO,
            authorization_scopes=[f'{resource_path}/{scope_name}']
        )

        method_resource = method.node.find_child('Resource')
        method_resource.add_property_override('AuthorizerId', {'Ref': authorizer.logical_id})


app = core.App()

PrintPostStack(
    app, stack_name,
    env={
        "region": os.environ["CDK_DEFAULT_REGION"],
        "account": os.environ["CDK_DEFAULT_ACCOUNT"]
    }
)

app.synth()