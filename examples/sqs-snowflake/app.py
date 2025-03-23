import json
import os
import typing as t

import dlt
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities import parameters
from aws_lambda_powertools.utilities.data_classes import (
    SQSEvent,
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
@event_source(data_class=SQSEvent)
def lambda_handler(event: SQSEvent, context: LambdaContext) -> t.Dict[str, t.Any]:
    if not event.records:
        logger.info("No content")
        return {"statusCode": 204, "body": "No content", "isBase64Encoded": False}

    logger.info("Processing records...")
    dlt.config["destination.filesystem.bucket_url"] = os.environ["DESTINATION_BUCKET"]

    p = dlt.pipeline(
        pipeline_name="lambda",
        dataset_name="dlt-sqs-snowflake-example",
        # staging="filesystem", # don't use staging for snowflake as it would require an extra stage to be created in Snowflake
        destination=snowflake(
            credentials=ASM_PROVIDER.get("DLT_SNOWFLAKE_CREDENTIALS", transform="json"),
            query_tag='{{"source":"{source}", "resource":"{resource}", "table": "{table}", "load_id":"{load_id}", "pipeline_name":"{pipeline_name}"}}',
            stage="dlt_sqs_snowflake_example",
        ),
        progress="log",
    )

    @dlt.resource(table_name="raw", write_disposition="append")
    def resource():
        count = 0
        for record in event.records:
            data = json.loads(record.body)
            yield data
            count += 1
        logger.info(f"Processed {count} records.")

    _ = p.run(resource())

    return {"statusCode": 200, "body": "Success", "isBase64Encoded": False}
