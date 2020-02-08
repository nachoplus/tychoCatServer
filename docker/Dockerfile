FROM bitnami/minideb:buster as builder

RUN install_packages gcc g++ make swig python3-dev python3-setuptools python3-pip cython wget pkg-config python3-venv

RUN python3 -m venv  --symlinks /app/venv
ENV PATH="/app/venv/bin:$PATH"

COPY requirements.txt /app/
RUN pip3 install wheel 
RUN pip3 install -r  /app/requirements.txt 
COPY / /app
WORKDIR /app
RUN ["python3","code/bootstrap.py"]


FROM bitnami/minideb:buster as runtime
RUN install_packages python3-minimal libpython3.7 wget 
COPY --from=builder /app /app
WORKDIR /app
ENV PATH="/app/venv/bin:$PATH"
ENTRYPOINT ["python3"]
CMD  ["code/tychoCatServer.py"]

