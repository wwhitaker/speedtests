FROM python:3.11-slim-trixie
LABEL maintainer="speedtests@email.defingo.net"
LABEL org.opencontainers.image.description="Original by Aiden Gilmartin. Speedtest to InfluxDB2 data bridge" 
LABEL org.opencontainers.image.source=https://github.com/wwhitaker/speedtests

ENV DEBIAN_FRONTEND=noninteractive

WORKDIR /app

# Install dependencies
RUN apt-get update \
	&& apt-get -q -y install --no-install-recommends ca-certificates curl dirmngr gnupg \
	&& curl -fsSL https://packagecloud.io/install/repositories/ookla/speedtest-cli/script.deb.sh | bash \
	&& apt-get -q -y install --no-install-recommends speedtest \
	&& apt-get -q -y autoremove \
	&& apt-get -q -y clean \
	&& rm -rf /var/lib/apt/lists/*

# Install python modules
COPY requirements.txt ./
RUN python -m pip install --no-cache-dir --upgrade pip \
	&& python -m pip install --no-cache-dir -r requirements.txt

# Final setup & execution
COPY main.py ./
CMD ["python", "main.py"]
