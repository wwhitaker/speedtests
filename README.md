# Speedtest to InfluxDB v2.0

This is a Python script that will continuously run the official Speedtest CLI application by Ookla, takes input from environment variables, formats data and writes it to an InfluxDB database.

This script will allow you to measure your internet connections speed and consistency over time. It uses env variables as configuration. It's as easy to use as telling your Docker server a 1 line command and you'll be set. Using Grafana you can start exploring this data easily.

This repository contains an InfluxQA based Grafana dashboard `GrafanaDash-SpeedTests.json` configuration. To make use of this please follow the InfluxDB guide for managing Grafana and InfluxQL data sources [here](https://docs.influxdata.com/influxdb/v2.0/tools/grafana/?t=InfluxQL).

![GrafanaDashboard](https://user-images.githubusercontent.com/945191/105287048-46f52a80-5b6c-11eb-9e57-038d63b67efb.png)

There are some added features to allow some additional details that Ookla provides as tags on your data. Some examples are your current ISP, the interface being used, the server who hosted the test. Overtime, you could identify if some serers are performing better than others.

## Acknowledgements

This work is based upon forks from:

- [davidtaddei](https://github.com/davidtaddei/speedtest_ookla-to-influxdbv2)
- [Qlustor](https://github.com/qlustor/speedtest_ookla-to-influxdb)
- [breadlysm](https://github.com/breadlysm/speedtest-to-influxdb)
- [Martin Francois](https://github.com/martinfrancois/speedtest-to-influxdb)
- [Aiden Gilmartin](https://github.com/aidengilmartin/speedtest-to-influxdb)

I have been a long time fan and user of this tool, primarily the docker container from [breadlysm](https://github.com/breadlysm/speedtest-to-influxdb).  As such, I had a long history of data to migrate to a new InfluxDB2 server.  Coupled with a desire for a multi-architecture container (amd64 and arm64) this repository was started.

## Preparing InfluxDB

Before configuring the speedtest container you must prepare a `speedtests` data [bucket](https://docs.influxdata.com/influxdb/v2.0/organizations/buckets/create-bucket/) and API token.

Also follow the additional instructions for using Grafana with [InfluxQL](https://docs.influxdata.com/influxdb/v2.0/tools/grafana/?t=InfluxQL).

## Configuring the container

The InfluxDB connection settings are controlled by environment variables.

The variables available are:

- NAMESPACE = default - None
- INFLUX_DB_ADDRESS = default - influxdb
- INFLUX_DB_PORT = default - 8086
- INFLUX_DB_ORG = default - {blank}
- INFLUX_DB_TOKEN = default - {blank}
- INFLUX_DB_DATABASE = default - speedtests
- INFLUX_DB_TAGS = default - None *See below for options, '\*' widcard for all*
- SPEEDTEST_INTERVAL = default - 5 (minutes)
- SPEEDTEST_FAIL_INTERVAL = default 5 (minutes)
- SPEEDTEST_SERVER_ID = default - {blank} *id from [Speedtest Static Servers](https://c.speedtest.net/speedtest-servers-static.php)*
- PING_INTERVAL = default - 5 (seconds)
- PING_TARGETS = default - 1.1.1.1, 8.8.8.8 (csv of hosts to ping)

### Variable Notes

- Intervals are in minutes. *Script will convert it to seconds.*
- If any variables are not needed, don't declare them. Functions will operate with or without most variables.
- Tags should be input without quotes. *INFLUX_DB_TAGS = isp, interface, external_ip, server_name, speedtest_url*
- NAMESPACE is used to collect data from multiple instances of the container into one database and select which you wish to view in Grafana. i.e. I have one monitoring my Starlink, the other my TELUS connection.

### Tag Options

The Ookla speedtest app provides a nice set of data beyond the upload and download speed. The list is below.

| Tag Name  | Description  |
|- |- |
| isp  | Your connections ISP  |
| interface  | Your devices connection interface  |
| internal_ip  | Your container or devices IP address  |
| interface_mac  | Mac address of your devices interface  |
| vpn_enabled  | Determines if VPN is enabled or not? I wasn't sure what this represented  |
| external_ip  | Your devices external IP address  |
| server_id  | The Speedtest ID of the server that  was used for testing  |
| server_name  | Name of the Speedtest server used  for testing  |
| server_country  | Country where the Speedtest server  resides  |
| server_location | Location where the Speedtest server  resides  |
| server_host  | Hostname of the Speedtest server  |
| server_port  | Port used by the Speedtest server  |
| server_ip  | Speedtest server's IP address  |
| speedtest_id  | ID of the speedtest results. Can be  used on their site to see results  |
| speedtest_url  | Link to the testing results. It provides your results as it would if you tested on their site.   |

### Additional Notes

Be aware that this script will automatically accept the license and GDPR statement so that it can run non-interactively. Make sure you agree with them before running.

## Docker

The container image is available through GitHub Containers.  Builds for amd64 and arm64 are included.

```shell
docker pull ghcr.io/wwhitaker/speedtests:latest
```

## Docker Compose

1. Configure the supplied `docker-compose.yml` file environment variables
2. Run `docker-compose up -d` to build the stack
3. Run `docker-compose down` to destroy the stack

You may also run InfluxDB as a container in the same stack. Setting the InfluxDB `container_name` will allow the speedtest container to communicate via hostnames.

## Migrate InfluxDB v1 to v2

Various methods exist to migrate data, but the simple approach below worked for me.

1. From the InfluxDB v1 server, export speedtests data to a line protocol file.

    ```shell
    influx_inspect export -datadir /var/lib/influxdb/data \
      -waldir /var/lib/influxdb/wal -database speedtests \
      -out speedtests.lp -lponly
    ```

2. Copy the speedtests.lp file to the InfluxDB2 server.
3. Import speedtests data into the speedtests bucket.

    ```shell
    influx write --bucket speedtests --file speedtests.lp
    ```
