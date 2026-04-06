import json
import unittest
from unittest.mock import Mock, patch

import main


class SpeedtestSmokeTests(unittest.TestCase):
    def test_speedtest_writes_results_and_closes_client(self):
        fake_client = Mock()
        fake_write_api = Mock()
        speedtest_payload = {
            "timestamp": "2026-04-06T02:30:00Z",
            "isp": "Example ISP",
            "interface": {
                "name": "eth0",
                "internalIp": "192.168.1.10",
                "macAddr": "00:11:22:33:44:55",
                "isVpn": False,
                "externalIp": "203.0.113.10",
            },
            "server": {
                "id": 1234,
                "name": "Example Server",
                "location": "Durham",
                "country": "US",
                "host": "example.invalid",
                "port": 8080,
                "ip": "198.51.100.10",
            },
            "result": {
                "id": "result-id",
                "url": "https://www.speedtest.net/result/c/result-id",
            },
            "ping": {
                "jitter": 1.23,
                "latency": 15.6,
            },
            "download": {
                "bandwidth": 62500000,
                "bytes": 1000,
                "elapsed": 100,
            },
            "upload": {
                "bandwidth": 12500000,
                "bytes": 500,
                "elapsed": 80,
            },
            "packetLoss": 0,
        }

        completed_process = Mock(
            returncode=0,
            stdout=json.dumps(speedtest_payload).encode("utf-8"),
            stderr=b"",
        )

        with patch.object(main, "create_write_api", return_value=(fake_client, fake_write_api)):
            with patch.object(main.subprocess, "run", return_value=completed_process):
                main.speedtest()

        fake_write_api.write.assert_called_once()
        fake_client.close.assert_called_once()

    def test_pingtest_writes_results_and_closes_client(self):
        fake_client = Mock()
        fake_write_api = Mock()

        first_response = Mock(error_message=None)
        second_response = Mock(error_message=None)
        first_ping = Mock(_responses=[first_response], rtt_avg_ms=12.34)
        second_ping = Mock(_responses=[second_response], rtt_avg_ms=56.78)

        with patch.object(main, "create_write_api", return_value=(fake_client, fake_write_api)):
            with patch.object(main, "PING_TARGETS", "1.1.1.1, 8.8.8.8"):
                with patch.object(main, "ping", side_effect=[first_ping, second_ping]):
                    main.pingtest()

        self.assertEqual(fake_write_api.write.call_count, 2)
        fake_client.close.assert_called_once()


if __name__ == "__main__":
    unittest.main()