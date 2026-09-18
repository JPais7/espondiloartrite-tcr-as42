FROM nvidia/cuda:12.8.1-cudnn-runtime-ubuntu24.04

ARG DEBIAN_FRONTEND=noninteractive
RUN apt-get update && apt-get install -y --no-install-recommends \
    git python3 python3-venv python3-pip ca-certificates curl && \
    rm -rf /var/lib/apt/lists/*

RUN python3 -m venv /opt/pilot-env
ENV PATH=/opt/pilot-env/bin:$PATH
RUN pip install --upgrade pip && \
    pip install "torch==2.14.0" && \
    pip install "rc-foundry[all] @ git+https://github.com/fnachon/foundry.git@a24335323b8fe8a927319d47b10f5bffffc17969"

WORKDIR /workspace
ENV FOUNDRY_CHECKPOINT_DIRS=/checkpoints
CMD ["bash"]
