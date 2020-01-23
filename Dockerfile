FROM python:3.7.0-stretch
RUN apt-get install -y gcc 
COPY requirements.txt /app/
RUN pip3 install -r  /app/requirements.txt 
COPY / /app
WORKDIR /app
ENTRYPOINT ["python3"]
CMD  ["tychoCatServer.py"]

