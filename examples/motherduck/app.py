import json
import os
import typing as t

import dlt
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEventV2,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from dlt.destinations.impl.motherduck.factory import motherduck

ASM_PROVIDER = parameters.SecretsProvider(
    Config(
        region_name=os.environ[
            "AWS_REGION"  # a default environment variable on AWS Lambda
        ]
    )
)


@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(
    event: APIGatewayProxyEventV2, context: LambdaContext
) -> t.Dict[str, t.Any]:
    if not event.body:
        return {"statusCode": 204, "body": "No content", "isBase64Encoded": False}

    p = dlt.pipeline(
        pipeline_name="lambda",
        dataset_name="lambda",
        destination=motherduck(
            credentials=ASM_PROVIDER.get("DLT_MOTHERDUCK_CREDENTIALS", transform="json")
        ),
        progress="log",
    )
    data = [json.loads(event.body)]
    _ = p.run(data, table_name="raw")

    return {"statusCode": 200, "body": "Success", "isBase64Encoded": False}
