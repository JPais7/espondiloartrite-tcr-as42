FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ARG DEBIAN_FRONTEND=noninteractive
ARG PILOT_GIT_COMMIT=unknown
LABEL org.opencontainers.image.revision=$PILOT_GIT_COMMIT
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-venv python3-pip ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pilot-env
ENV PATH=/opt/pilot-env/bin:$PATH
COPY cloud/requirements-core.txt /tmp/requirements-core.txt
RUN pip install --upgrade pip && \
    pip install "torch==2.14.0" && \
    pip install "rc-foundry[all] @ git+https://github.com/fnachon/foundry.git@a24335323b8fe8a927319d47b10f5bffffc17969" && \
    pip install -r /tmp/requirements-core.txt && \
    pip check

WORKDIR /workspace
ENV FOUNDRY_CHECKPOINT_DIRS=/checkpoints
CMD ["bash"]
