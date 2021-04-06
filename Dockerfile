FROM python:3.8-slim-buster
LABEL maintainer="Team QLUSTOR <team@qlustor.com>" \
    description="Original by Aiden Gilmartin. Speedtest to InfluxDB data bridge"

ENV DEBIAN_FRONTEND noninteractive

RUN apt-get update && \
    apt-get install -y --no-install-recommends apt-utils gnupg1 apt-transport-https dirmngr && \
    apt-get -q -y autoremove && apt-get -q -y clean && \
    rm -rf /var/lib/apt/lists/

RUN apt-key adv --keyserver keyserver.ubuntu.com --recv-keys 379CE192D401AB61 && \
  echo "deb https://ookla.bintray.com/debian buster main" > /etc/apt/sources.list.d/speedtest.list && \
  apt-get update && apt-get -q -y install speedtest && \
  apt-get -q -y autoremove && apt-get -q -y clean && \
  rm -rf /var/lib/apt/lists/

WORKDIR /app

ADD requirements.txt .

RUN pip install --no-cache -r requirements.txt

# Final setup & execution
ADD main.py .
CMD ["main.py"]
