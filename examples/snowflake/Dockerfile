# see https://dev.l1x.be/posts/2023/02/28/using-python-3.11-with-aws-lambda/
FROM python:3.12.7-slim-bullseye AS builder

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
    g++ \
    make \
    cmake \
    unzip \
    libcurl4-openssl-dev && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

ENV LAMBDA_TASK_ROOT=/var/task
RUN mkdir -p ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}

RUN python -m venv .venv 
ENV PATH=${LAMBDA_TASK_ROOT}/.venv/bin:$PATH
RUN which pip && \
    pip install pip --upgrade && \
    pip install --no-cache-dir -U awslambdaric setuptools poetry==1.8.2

# Copy & install requirements.txt
COPY pyproject.toml ${LAMBDA_TASK_ROOT}
COPY poetry.lock ${LAMBDA_TASK_ROOT}

RUN cd ${LAMBDA_TASK_ROOT} && \
    poetry export -o requirements.txt --without-hashes && \
    pip install --no-cache-dir -r requirements.txt

FROM python:3.12.7-slim-bullseye AS runner

ENV LAMBDA_TASK_ROOT=/var/task

RUN mkdir -p ${LAMBDA_TASK_ROOT}
WORKDIR ${LAMBDA_TASK_ROOT}
COPY --from=builder ${LAMBDA_TASK_ROOT} ${LAMBDA_TASK_ROOT}

ENV PATH=${LAMBDA_TASK_ROOT}/.venv/bin:$PATH

# Copy function code
COPY app.py ${LAMBDA_TASK_ROOT}/app.py

ENTRYPOINT [ "python", "-m", "awslambdaric" ]
CMD [ "app.lambda_handler" ]
