import json
import requests
import socket
from threading import Thread
import time
import unittest
import xml.etree.ElementTree as ElementTree

from netargparse import NetArgumentParser


def tcp_socket_no_autoformat():
    def main(args):
        return f'"{args}"'

    nap = NetArgumentParser()
    nap.parser.add_argument("--var_str", type=str)
    nap.parser.add_argument("--var_int", type=int)
    nap.parser.add_argument("--var_true", action="store_true")
    nap(main, False, 0.2, ["nap", "--port", "7000"])

def tcp_socket_autoformat():
    def main(args):
        return vars(args)

    nap = NetArgumentParser()
    nap.parser.add_argument("--var_str", type=str)
    nap.parser.add_argument("--var_int", type=int)
    nap.parser.add_argument("--var_true", action="store_true")
    nap(main, resp_delay=0.2, parse_args=["nap", "--port", "7001"])

def http_no_autoformat():
    def main(args):
        return f'"{args}"'

    nap = NetArgumentParser()
    nap.parser.add_argument("--var_str", type=str)
    nap.parser.add_argument("--var_int", type=int)
    nap.parser.add_argument("--var_true", action="store_true")
    nap(main, False, 0.2, ["nap", "--port", "7002", "--http"])

def http_autoformat():
    def main(args):
        return vars(args)

    nap = NetArgumentParser()
    nap.parser.add_argument("--var_str", type=str)
    nap.parser.add_argument("--var_int", type=int)
    nap.parser.add_argument("--var_true", action="store_true")
    nap(main, resp_delay=0.2, parse_args=["nap", "--port", "7003", "--http"])


class TcpSocketRequest:
    def __init__(self, port):
        self.s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.s.connect(("localhost", port))

    def txrx(self, msg):
        self.s.sendall(msg)
        recv = self.s.recv(1024)
        return recv

class HttpRequest:
    def __init__(self, port):
        self.port = port
        requests.get(f"http://localhost:{self.port}")

    def txrx(self, msg):
        recv = requests.get(f"http://localhost:{self.port}{msg}")
        return recv.text


class TestNetArgumentParser(unittest.TestCase):
    def assertResponse(self, resp, resp_type):
        try:
            if resp_type == "xml":
                ElementTree.fromstring(resp)
            elif resp_type == "json":
                json.loads(resp)
            else:
                raise Exception(f"Wrong resp_type '{resp_type}' given.")
        except Exception as e:
            self.fail(e)

    def test_plain_xml_na_valid_tx(self):
        ans = s_tcp_na.txrx(b"<nap><__var_str>value</__var_str><__var_int>2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response>\"Namespace(var_str='value', var_int=2, var_true=False, _cmd='nap')\"</response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_na_valid_tx_with_var_true(self):
        ans = s_tcp_na.txrx(b"<nap><__var_str>value</__var_str><__var_int>0</__var_int><__var_true></__var_true></nap>")
        self.assertEqual(ans, b"<nap><response>\"Namespace(var_str='value', var_int=0, var_true=True, _cmd='nap')\"</response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_na_invalid_int(self):
        ans = s_tcp_na.txrx(b"<nap><__var_str>value</__var_str><__var_int>2.2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response></response><exception>argument --var_int: invalid int value: '2.2'</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_json_na_valid_tx(self):
        ans = s_tcp_na.txrx(b'{"--var_str": "value", "--var_int": "2"}')
        self.assertEqual(ans, b'{"response": "Namespace(var_str=\'value\', var_int=2, var_true=False, _cmd=\'nap\')", "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_na_valid_tx_with_var_true(self):
        ans = s_tcp_na.txrx(b'{"--var_str": "value", "--var_int": "0", "--var_true": ""}')
        self.assertEqual(ans, b'{"response": \"Namespace(var_str=\'value\', var_int=0, var_true=True, _cmd=\'nap\')\", "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_na_invalid_int(self):
        ans = s_tcp_na.txrx(b'{"--var_str": "value", "--var_int": "2.2"}')
        self.assertEqual(ans, b'{"response": "", "exception": "argument --var_int: invalid int value: \'2.2\'", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_xml_a_valid_tx(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>value</__var_str><__var_int>2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response><var_str>value</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_valid_tx_with_var_true(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>value</__var_str><__var_int>0</__var_int><__var_true></__var_true></nap>")
        self.assertEqual(ans, b"<nap><response><var_str>value</var_str><var_int>0</var_int><var_true>True</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_invalid_int(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>value</__var_str><__var_int>2.2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response></response><exception>argument --var_int: invalid int value: '2.2'</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_json_a_valid_tx(self):
        ans = s_tcp_a.txrx(b'{"--var_str": "value", "--var_int": "2"}')
        self.assertEqual(ans, b'{"response": {"var_str": "value", "var_int": 2, "var_true": false, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_valid_tx_with_var_true(self):
        ans = s_tcp_a.txrx(b'{"--var_str": "value", "--var_int": 4, "--var_true": ""}')
        self.assertEqual(ans, b'{"response": {"var_str": "value", "var_int": 4, "var_true": true, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_invalid_int(self):
        ans = s_tcp_a.txrx(b'{"--var_str": "value", "--var_int": "2.2"}')
        self.assertEqual(ans, b'{"response": "", "exception": "argument --var_int: invalid int value: \'2.2\'", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_na_valid_tx(self):
        ans = s_http_na.txrx("/?--var_str=value&--var_int=2")
        self.assertEqual(ans, '{"response": "Namespace(var_str=\'value\', var_int=2, var_true=False, _cmd=\'nap\')", "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_na_valid_tx_with_var_true(self):
        ans = s_http_na.txrx("/?--var_str=value&--var_int=0&--var_true")
        self.assertEqual(ans, '{"response": "Namespace(var_str=\'value\', var_int=0, var_true=True, _cmd=\'nap\')", "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_na_invalid_int(self):
        ans = s_http_na.txrx("/?--var_str=value&--var_int=2.2")
        self.assertEqual(ans, '{"response": "", "exception": "argument --var_int: invalid int value: \'2.2\'", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_xml_na_valid_tx(self):
        ans = s_http_na.txrx("/xml?--var_str=value&--var_int=2")
        self.assertEqual(ans, "<nap><response>\"Namespace(var_str='value', var_int=2, var_true=False, _cmd='nap')\"</response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_na_valid_tx_with_var_true(self):
        ans = s_http_na.txrx("/xml?--var_str=value&--var_int=0&--var_true")
        self.assertEqual(ans, "<nap><response>\"Namespace(var_str='value', var_int=0, var_true=True, _cmd='nap')\"</response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_na_invalid_int(self):
        ans = s_http_na.txrx("/xml?--var_str=value&--var_int=2.2")
        self.assertEqual(ans, "<nap><response></response><exception>argument --var_int: invalid int value: '2.2'</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_json_a_valid_tx(self):
        ans = s_http_a.txrx("/?--var_str=value&--var_int=2")
        self.assertEqual(ans, '{"response": {"var_str": "value", "var_int": 2, "var_true": false, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_valid_tx_with_var_true(self):
        ans = s_http_a.txrx("/?--var_str=value&--var_int=0&--var_true")
        self.assertEqual(ans, '{"response": {"var_str": "value", "var_int": 0, "var_true": true, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_invalid_int(self):
        ans = s_http_a.txrx("/?--var_str=value&--var_int=2.2")
        self.assertEqual(ans, '{"response": "", "exception": "argument --var_int: invalid int value: \'2.2\'", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_xml_a_valid_tx(self):
        ans = s_http_a.txrx("/xml?--var_str=value&--var_int=2")
        self.assertEqual(ans, "<nap><response><var_str>value</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_valid_tx_with_var_true(self):
        ans = s_http_a.txrx("/xml?--var_str=value&--var_int=0&--var_true")
        self.assertEqual(ans, "<nap><response><var_str>value</var_str><var_int>0</var_int><var_true>True</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_invalid_int(self):
        ans = s_http_a.txrx("/xml?--var_str=value&--var_int=2.2")
        self.assertEqual(ans, "<nap><response></response><exception>argument --var_int: invalid int value: '2.2'</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")


if __name__ == "__main__":
    for t in [tcp_socket_no_autoformat, tcp_socket_autoformat, http_no_autoformat, http_autoformat]:
        Thread(target=t, daemon=True).start()

    for i in range(10):
        if i == 9:
            raise ConnectionRefusedError()
        try:
            if not "s_tcp_na" in globals():
                s_tcp_na = TcpSocketRequest(7000)
            if not "s_tcp_a" in globals():
                s_tcp_a = TcpSocketRequest(7001)
            if not "s_http_na" in globals():
                s_http_na = HttpRequest(7002)
            if not "s_http_a" in globals():
                s_http_a = HttpRequest(7003)
            break
        except (ConnectionRefusedError, requests.exceptions.ConnectionError):
            time.sleep(1)

    unittest.main()
