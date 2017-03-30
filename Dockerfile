FROM ubuntu
RUN apt-get update &&  apt-get install -y python python-pip python-dev
RUN apt-get install -y swig unzip
COPY requirements.txt /usr/src/app/
RUN pip install -r  /usr/src/app/requirements.txt
CMD [ "python", "./CatServer.py" ]

