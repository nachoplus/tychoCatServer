FROM python:3.7.0-stretch
RUN apt-get install -y gcc make
COPY requirements.txt /app/
RUN pip3 install -r  /app/requirements.txt 
COPY / /app
WORKDIR /app
RUN ["python3","/app/bootstrap.py"]
ENTRYPOINT ["python3"]
CMD  ["tychoCatServer.py"]

