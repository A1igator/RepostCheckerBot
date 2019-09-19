FROM nitincypher/docker-ubuntu-python-pip

ADD app.py /
ADD config.py /
ADD database.py /
ADD setInterval.py /
ADD requirements.txt /

RUN pip install -r ./requirements.txt

CMD [ "python", "./app.py" ]