FROM ubuntu:18.04

ADD app.py /
ADD config.py /
ADD database.py /
ADD setInterval.py /
ADD requirements.txt /

RUN \
  apt-get update && \
  apt-get -y upgrade

RUN apt-get install -y \
    python3 python3-pip python3-dev pkg-config \
    libavformat-dev libavcodec-dev libavdevice-dev \
    libavutil-dev libswscale-dev libswresample-dev libavfilter-dev

RUN pip3 install -r ./requirements.txt

ARG BOT_CLIENT_ID
ARG BOT_CLIENT_SECRET
ARG BOT_USER_AGENT
ARG BOT_USERNAME
ARG BOT_PASSWORD
ARG BOT_SUB_COUNT
ARG BOT_SUBREDDIT0

ENV BOT_CLIENT_ID=$BOT_CLIENT_ID
ENV BOT_CLIENT_SECRET=$BOT_CLIENT_SECRET
ENV BOT_USER_AGENT=$BOT_USER_AGENT
ENV BOT_USERNAME=$BOT_USERNAME
ENV BOT_PASSWORD=$BOT_PASSWORD
ENV BOT_SUB_COUNT=$BOT_SUB_COUNT
ENV BOT_SUBREDDIT0=$BOT_SUBREDDIT0

CMD [ "python3", "./app.py" ]