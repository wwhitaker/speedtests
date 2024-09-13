FROM python:3.11-slim-bookworm
LABEL maintainer="speedtests@email.defingo.net"
LABEL org.opencontainers.image.description "Original by Aiden Gilmartin. Speedtest to InfluxDB2 data bridge" 
LABEL org.opencontainers.image.source https://github.com/wwhitaker/speedtests

ENV DEBIAN_FRONTEND noninteractive

# Install dependencies
RUN apt-get update 
RUN apt-get -q -y install --no-install-recommends apt-utils gnupg1 apt-transport-https dirmngr curl

# Install Speedtest
RUN curl -s https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash
RUN apt-get -q -y install speedtest

# Clean up
RUN apt-get -q -y autoremove && apt-get -q -y clean 
RUN rm -rf /var/lib/apt/lists/*

WORKDIR /app

ADD requirements.txt .

RUN pip install --no-cache -r requirements.txt

# Final setup & execution
ADD main.py .
CMD ["python", "main.py"]
