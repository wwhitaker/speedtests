# import datetime
import json
import os
import subprocess
import time
from multiprocessing import Process

from influxdb_client import InfluxDBClient, Point, WritePrecision
from influxdb_client.client.write_api import SYNCHRONOUS
from pythonping import ping

# InfluxDB Settings
NAMESPACE = os.getenv("NAMESPACE", "None")
DB_ADDRESS = os.getenv("INFLUX_DB_ADDRESS", "influxdb")
DB_PORT = int(os.getenv("INFLUX_DB_PORT", "8086"))
DB_ORG = os.getenv("INFLUX_DB_ORG", "")
DB_TOKEN = os.getenv("INFLUX_DB_TOKEN", "")
DB_BUCKET = os.getenv("INFLUX_DB_BUCKET", "speedtests")
DB_TAGS = os.getenv("INFLUX_DB_TAGS", None)
PING_TARGETS = os.getenv("PING_TARGETS", "1.1.1.1, 8.8.8.8")

# Speedtest Settings
# Time between tests (in minutes, converts to seconds).
TEST_INTERVAL = int(os.getenv("SPEEDTEST_INTERVAL", "180")) * 60
# Specific server ID
SERVER_ID = os.getenv("SPEEDTEST_SERVER_ID", "")
# Time between ping tests (in seconds).
PING_INTERVAL = int(os.getenv("PING_INTERVAL", "120"))

client = InfluxDBClient(
    url=f"{DB_ADDRESS}:{DB_PORT}", token=f"{DB_TOKEN}", org=f"{DB_ORG}"
)

write_api = client.write_api(write_options=SYNCHRONOUS)
query_api = client.query_api()

def pkt_loss(data):
    if "packetLoss" in data.keys():
        return int(data["packetLoss"])
    else:
        return 0


def tag_selection(data):
    tags = DB_TAGS
    options = {}

    # tag_switch takes in _data and attaches CLIoutput to more readable ids
    tag_switch = {
        "namespace": NAMESPACE,
        "isp": data["isp"],
        "interface": data["interface"]["name"],
        "internal_ip": data["interface"]["internalIp"],
        "interface_mac": data["interface"]["macAddr"],
        "vpn_enabled": (False if data["interface"]["isVpn"] == "false" else True),
        "external_ip": data["interface"]["externalIp"],
        "server_id": data["server"]["id"],
        "server_name": data["server"]["name"],
        "server_location": data["server"]["location"],
        "server_country": data["server"]["country"],
        "server_host": data["server"]["host"],
        "server_port": data["server"]["port"],
        "server_ip": data["server"]["ip"],
        "speedtest_id": data["result"]["id"],
        "speedtest_url": data["result"]["url"],
    }

    if tags is None:
        tags = "namespace"
    elif "*" in tags:
        return tag_switch
    else:
        tags = "namespace, " + tags

    tags = tags.split(",")
    for tag in tags:
        # split the tag string, strip and add selected tags to {options} with corresponding tag_switch data
        tag = tag.strip()
        options[tag] = tag_switch[tag]

    return options


def format_for_influx(data):

    # There is additional data in the speedtest-cli output but it is likely not necessary to store.
    influx_data = [
        Point("ping")
        .field("jitter", data["ping"]["jitter"])
        .field("latency", data["ping"]["latency"])
        .time(data["timestamp"], WritePrecision.MS),
        Point("download")
        .field("bandwidth", (data["download"]["bandwidth"] / 125000))
        .field("bytes", data["download"]["bytes"])
        .field("elapsed", data["download"]["elapsed"])
        .time(data["timestamp"], WritePrecision.MS),
        Point("upload")
        .field("bandwidth", (data["upload"]["bandwidth"] / 125000))
        .field("bytes", data["upload"]["bytes"])
        .field("elapsed", data["upload"]["elapsed"])
        .time(data["timestamp"], WritePrecision.MS),
        Point("packetloss")
        .field("packetLoss", pkt_loss(data))
        .time(data["timestamp"], WritePrecision.MS),
        Point("speeds")
        .field("jitter", data["ping"]["jitter"])
        .field("latency", data["ping"]["latency"])
        .field("packetLoss", pkt_loss(data))
        .field("bandwidth_down", (data["download"]["bandwidth"] / 125000))
        .field("bytes_down", data["download"]["bytes"])
        .field("elapsed_down", data["download"]["elapsed"])
        .field("bandwidth_up", (data["upload"]["bandwidth"] / 125000))
        .field("bytes_up", data["upload"]["bytes"])
        .field("elapsed_up", data["upload"]["elapsed"])
        .time(data["timestamp"], WritePrecision.MS),
    ]

    tags = tag_selection(data)
    if tags is not None:
        for measurement in influx_data:
            for k, v in tags.items():
                measurement.tag(k, v)

    return influx_data


def speedtest():
    if not SERVER_ID:
        speedtest = subprocess.run(
            ["speedtest", "--accept-license", "--accept-gdpr", "-f", "json"],
            capture_output=True,
        )
        print("Automatic server choice")
    else:
        speedtest = subprocess.run(
            [
                "speedtest",
                "--accept-license",
                "--accept-gdpr",
                "-f",
                "json",
                "--server-id=" + SERVER_ID,
            ],
            capture_output=True,
        )
        print("Manual server choice : ID = " + SERVER_ID)

    if speedtest.returncode == 0:  # Speedtest was successful.
        print("Speedtest Successful :")
        data_json = json.loads(speedtest.stdout)
        print(
            "time: "
            + str(data_json["timestamp"])
            + " - ping: "
            + str(data_json["ping"]["latency"])
            + " ms - download: "
            + str(data_json["download"]["bandwidth"] / 125000)
            + " Mb/s - upload: "
            + str(data_json["upload"]["bandwidth"] / 125000)
            + " Mb/s - isp: "
            + data_json["isp"]
            + " - ext. IP: "
            + data_json["interface"]["externalIp"]
            + " - server id: "
            + str(data_json["server"]["id"])
            + " ("
            + data_json["server"]["name"]
            + " @ "
            + data_json["server"]["location"]
            + ")"
        )
        data = format_for_influx(data_json)
        write_api.write(bucket=DB_BUCKET, record=data)
        print("Data written to DB successfully")
    else:  # Speedtest failed.
        print("Speedtest Failed :")
        print(speedtest.stderr)
        print(speedtest.stdout)


def pingtest():
    # timestamp = datetime.datetime.utcnow()
    for target in PING_TARGETS.split(","):
        target = target.strip()
        pingtest = ping(target, verbose=False, timeout=1, count=1, size=128)

        success = int(pingtest._responses[0].error_message is None)
        rtt = float(
            0
            if pingtest._responses[0].error_message is not None
            else pingtest.rtt_avg_ms
        )
        data = (
            Point("pings")
            .field("success", success)
            .field("rtt", rtt)
            .tag("namespace", NAMESPACE)
            .tag("target", target)
        )
        write_api.write(bucket=DB_BUCKET, record=data)


def main():
    pPing = Process(target=pingtest)
    pSpeed = Process(target=speedtest)

    # init_db()  # Setup the database if it does not already exist.

    loop_count = 0
    while 1:  # Run a Speedtest and send the results to influxDB indefinitely.
        if loop_count == 0 or loop_count % PING_INTERVAL == 0:
            if pPing.is_alive():
                pPing.terminate()
            pPing = Process(target=pingtest)
            pPing.start()

        if loop_count == 0 or loop_count % TEST_INTERVAL == 0:
            if pSpeed.is_alive():
                pSpeed.terminate()
            pSpeed = Process(target=speedtest)
            pSpeed.start()

        if loop_count % (PING_INTERVAL * TEST_INTERVAL) == 0:
            loop_count = 0

        time.sleep(1)
        loop_count += 1


if __name__ == "__main__":
    print("Speedtest CLI data logger to InfluxDB started...")
    main()
