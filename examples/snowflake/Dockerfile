FROM public.ecr.aws/lambda/python:3.11 AS build


# Copy & install requirements.txt
COPY requirements.txt ${LAMBDA_TASK_ROOT}/requirements.txt

RUN cd ${LAMBDA_TASK_ROOT} && \
    pip install -r requirements.txt

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}/app.py

WORKDIR ${LAMBDA_TASK_ROOT}
ENV PATH=${LAMBDA_TASK_ROOT}:${PATH}

CMD [ "app.lambda_handler" ]
