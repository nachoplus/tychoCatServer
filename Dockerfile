FROM python:3.7-slim
COPY requirements.txt /usr/src/app/
RUN pip install -r  /usr/src/app/requirements.txt 
COPY / /usr/src/app/
RUN  cd /usr/src/app/ && /usr/src/app/bootstrap.py
CMD  cd /usr/src/app/ && /usr/src/app/CatServer.py
