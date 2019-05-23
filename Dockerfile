FROM python:3.7.0-stretch
COPY requirements.txt /usr/src/app/
RUN apt-get install -y gcc
RUN pip install -r  /usr/src/app/requirements.txt 
COPY / /usr/src/app/
RUN  cd /usr/src/app/ && /usr/src/app/bootstrap.py
CMD  cd /usr/src/app/ && /usr/src/app/tychoCatServer.py

