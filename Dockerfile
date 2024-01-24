FROM python:3.12-slim

# general approach shamelessly lifted from the Python Docker Hub documentation
WORKDIR /usr/src/app

RUN apt-get update \
    && apt-get install -y curl 
        # python3-yaml # this doesn't let you import yaml. no clue what this is.

# wanted to use speedtest-cli but it's server list is like a top 10, not a full list.
# it won't see beyond that nor could I find authoritative lists for a PR.
# Speedtest's own app had the serers I wanted coming back
RUN curl -o /tmp/speedtest.tgz https://install.speedtest.net/app/cli/ookla-speedtest-1.2.0-linux-x86_64.tgz \
    && tar -xvf /tmp/speedtest.tgz -C /tmp/ \
    && mv /tmp/speedtest /usr/bin/speedtest

COPY requirements.txt ./
RUN pip3 install --no-cache-dir -r requirements.txt

COPY . .

CMD [ "python", "./monitor.py" ]