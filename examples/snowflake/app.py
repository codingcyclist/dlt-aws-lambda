import json
import os
import typing as t

import dlt
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.data_classes import (
    APIGatewayProxyEventV2,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from botocore.config import Config
from dlt.destinations.impl.snowflake.factory import snowflake

ASM_PROVIDER = parameters.SecretsProvider(
    Config(
        region_name=os.environ[
            "AWS_REGION"  # a default environment variable on AWS Lambda
        ]
    )
)

logger = Logger()
tracer = Tracer()


@logger.inject_lambda_context(clear_state=True)
@tracer.capture_lambda_handler
@event_source(data_class=APIGatewayProxyEventV2)
def lambda_handler(
    event: APIGatewayProxyEventV2, context: LambdaContext
) -> t.Dict[str, t.Any]:
    if not event.body:
        return {"statusCode": 204, "body": "No content", "isBase64Encoded": False}

    p = dlt.pipeline(
        pipeline_name="lambda",
        dataset_name="lambda",
        destination=snowflake(
            credentials=ASM_PROVIDER.get("DLT_SNOWFLAKE_CREDENTIALS", transform="json"),
            query_tag='{{"source":"{source}", "resource":"{resource}", "table": "{table}", "load_id":"{load_id}", "pipeline_name":"{pipeline_name}"}}',
        ),
        progress="log",
    )
    data = [json.loads(event.body)]
    _ = p.run(data, table_name="raw")

    return {"statusCode": 200, "body": "Success", "isBase64Encoded": False}
