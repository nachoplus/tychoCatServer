FROM debian:buster as builder

RUN apt update && apt install -y --no-install-recommends gcc g++ make swig python3-dev python3-setuptools python3-pip cython wget pkg-config python3-venv  && apt clean && rm -rf /var/lib/apt/lists/*

RUN python3 -m venv  --symlinks /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt /app/
RUN pip3 install wheel 
RUN pip3 install -r  /app/requirements.txt 
COPY / /app
WORKDIR /app
RUN ["python3","code/bootstrap.py"]


FROM debian:buster as runtime
RUN  apt update && apt install -y --no-install-recommends python3-minimal libpython3.7 wget && apt clean && rm -rf /var/lib/apt/lists/*
COPY --from=builder /app /app
WORKDIR /app
ENV PATH="/app/venv/bin:$PATH"
CMD  ["python3","code/tychoCatServer.py"]

