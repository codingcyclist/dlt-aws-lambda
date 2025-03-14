import json
import os
import typing as t

import dlt
from aws_lambda_powertools.logging import Logger
from aws_lambda_powertools.tracing import Tracer
from aws_lambda_powertools.utilities.data_classes import (
    SQSEvent,
    event_source,
)
from aws_lambda_powertools.utilities.typing import LambdaContext
from dlt.common.configuration.specs.aws_credentials import AwsCredentials
from dlt.destinations.impl.athena.factory import athena

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
        dataset_name="dlt-athena-example",
        staging="filesystem",  # required for athena destination
        destination=athena(
            query_result_bucket=os.environ["DESTINATION_BUCKET"],
            athena_work_group="dlt",
            credentials=AwsCredentials(
                # picked-up automatically from the environment variables on AWS Lambda
                aws_access_key_id=os.environ["AWS_ACCESS_KEY_ID"],
                aws_secret_access_key=os.environ["AWS_SECRET_ACCESS_KEY"],
                aws_session_token=os.environ["AWS_SESSION_TOKEN"],
                region_name=os.environ["AWS_REGION"],
            ),
            aws_data_catalog="aws_data_catalog",
            truncate_tables_on_staging_destination_before_load=False,  # prevents truncation of shared staging files, see https://dlthub.com/docs/dlt-ecosystem/staging#how-to-prevent-staging-files-truncation
        ),
        progress="log",
    )

    @dlt.resource(table_name="raw")
    def resource():
        count = 0
        for record in event.records:
            data = json.loads(record.body)
            yield data
            count += 1
        logger.info(f"Processed {count} records.")

    _ = p.run(resource())

    return {"statusCode": 200, "body": "Success", "isBase64Encoded": False}
