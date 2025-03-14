# Running DLT on AWS Lambda

AWS Lambda is a pay-as-you-go compute service that lets you run code without provisioning or managing servers. Moreover, Lambda functions are particularly good at handling traffic volatility through built-in horizontal scaling.

[DLT](https://dlthub.com/docs/getting-started) fits neatly into the paradigm of AWS Lambda as it’s a lightweight python library that runs on any infrastructure. All it takes to build a powerful and scalable event ingestion engine is to add a simple REST API and a few lines of DLT script. Without breaking a sweat, you can leverage all the mighty abstractions of DLT (normalization, schema migration, provisioning of staging destinations) to create well-structured, live datasets out of arbitrary JSON objects.

## Secrets

DLT usually recommends providing database secrets either via TOML files or via environment variables ([docs](https://dlthub.com/docs/general-usage/credentials/configuration)). However, given that AWS Lambda does not support masking files or environment variables as secrets, both methods could easily leak confidential values. The recommended way for injecting confidential values into an AWS Lambda function is via AWS Secretsmanager (ASM). ASM secrets are simple key-value pairs, so you just need to create one ASM secret for all your destination credentials.

```shell
# create secret (Snowflake example)
# see: https://dlthub.com/docs/dlt-ecosystem/destinations/snowflake#authentication-types
aws secretsmanager create-secret \
    --name DLT_SNOWFLAKE_CREDENTIALS \
    --secret-string '{"database":"<your-db>","username":"<your-username>","warehouse":"<your-wh>","role":"<your-role>","host":"<your-host>","private_key":"<your-base64-encoded-private-key>","private_key_passphrase":"<your-private-key-passphrase>"}'

# or if you want to read the credentials from a local json file
aws secretsmanager create-secret \
    --name DLT_SNOWFLAKE_CREDENTIALS \
    --secret-string "$(cat credentials.json)"

# create secret (Motherduck example)
aws secretsmanager create-secret \
    --name DLT_MOTHERDUCK_CREDENTIALS \
    --secret-string '{"database":"<your-db>","password":"<your-service-token>"}'

# delete secret
aws secretsmanager delete-secret \
    --secret-id arn:aws:secretsmanager:<region>:<account-id>:secret:<secret-name> \
    --force-delete-without-recovery
```

## Getting started

All examples inside the `/examples` folder use AWS SAM to deploy DLT inside an AWS Lambda function. SAM is a lightweight Infrastructure-As-Code framework provided by AWS. Using SAM, you simply declare serverless resources like Lambda functions, API Gateways, etc. in a `.yml` file and deploy them to your AWS account with a lightweight CLI. Here's how to get started:

### Snowflake & Motherduck Examples

These are two simple examples of how to use DLT with AWS Lambda to load events sent to an API Gateway endpoint one-by-one into a data warehouse (Snowflake or Motherduck). See the SQS-Athena example for a more scalable approach with a buffer queue between the API Gateway and the Lambda function.

1. Install the SAM CLI
   ```bash
   pip install aws-sam-cli
   ```
2. Build a deployment package
   ```
   sam build
   ```
3. Test your setup locally

   ```bash
   sam local start-api

   >  * Running on http://127.0.0.1:3000

   # in a second terminal window
   curl -X POST http://127.0.0.1:3000/collect -d '{"hello":"world"}'

   > -------------------------------- Extract lambda --------------------------------
   > Resources: 1/1 (100.0%) | Time: 0.01s | Rate: 119.69/s
   > raw: 1  | Time: 0.01s | Rate: 133.59/s
   >
   > -------------------- Normalize lambda in 1701539812.689153 ---------------------
   > Files: 1/1 (100.0%) | Time: 0.37s | Rate: 2.74/s
   > Items: 1  | Time: 0.37s | Rate: 2.74/s
   >
   > ----------------------- Load lambda in 1701539812.689153 -----------------------
   > Jobs: 0/1 (0.0%) | Time: 0.00s | Rate: 0.00/s
   >
   > ----------------------- Load lambda in 1701539812.689153 -----------------------
   > Jobs: 1/1 (100.0%) | Time: 0.06s | Rate: 16.22/s
   >
   > ----------------------- Load lambda in 1701539812.689153 -----------------------
   >
   > END RequestId: 535b9277-de0a-43a9-b65f-def690c3975d
   > REPORT RequestId: 535b9277-de0a-43a9-b65f-def690c3975d  Init Duration: 1.62 ms  Duration: 17855.55 ms   Billed Duration: 17856 ms       Memory Size: 512 MB       Max Memory Used: 512 MB
   > No Content-Type given. Defaulting to 'application/json'.
   ```

4. Deploy your resources to AWS

   ```
   sam deploy --stack-name=<your-stack-name> --resolve-image-repos --resolve-s3 --capabilities CAPABILITY_IAM

   > ------------------------------------------------------------------------------------------------
   > Outputs
   > ------------------------------------------------------------------------------------------------
   > Key                 ApiGateway
   > Description         API Gateway endpoint URL for Staging stage for Hello World function
   > Value               https://ykvypgnm7g.execute-api.eu-central-1.amazonaws.com/v1/collect/
   > ------------------------------------------------------------------------------------------------
   ```

5. Invoke your deployed Lambda function

   ```
   curl -X POST https://ykvypgnm7g.execute-api.eu-central-1.amazonaws.com/v1/collect -d '{"hello":"world"}'
   ```

### SQS-Athena Example

This more sophisticated example on how to use DLT with AWS Lambda to load larger volumes of events sent to an API Gateway endpoint into a data lake (AWS Athena). What makes this example more scalable is that it uses a buffer queue to decouple the API Gateway from the Lambda function and load events in batches. It also leverages AWS Athena + AWS Glue to de-couple storage from compute, which is an additional leaver to reduce costs.

> Given the SQS queue, this example cannot be tested locally.

1. Install the SAM CLI
   ```bash
   pip install aws-sam-cli
   ```
2. Build a deployment package

   ```
   sam build
   ```

3. Deploy your resources to AWS

   ```
   sam deploy --stack-name=<your-stack-name> --resolve-image-repos --resolve-s3 --capabilities CAPABILITY_IAM

   > ------------------------------------------------------------------------------------------------
   > Outputs
   > ------------------------------------------------------------------------------------------------
   > Key                 ApiGateway
   > Description         API Gateway endpoint URL for Staging stage for Hello World function
   > Value               https://ykvypgnm7g.execute-api.eu-central-1.amazonaws.com/v1/collect/
   > ------------------------------------------------------------------------------------------------
   ```

4. Invoke your deployed Lambda function
   ```
   curl -X POST https://ykvypgnm7g.execute-api.eu-central-1.amazonaws.com/v1/collect -d '{"hello":"world"}'
   ```
