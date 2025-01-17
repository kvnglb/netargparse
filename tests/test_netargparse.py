import json
import requests
import socket
from threading import Thread
import time
import unittest
import xml.etree.ElementTree as ElementTree

from netargparse import NetArgumentParser


port_start = 7200

def tcp_socket_no_autoformat():
    def main(args):
        if args.var_str == "damn":
            return args.var_int / 0
        return f'"{args}"'

    parser = NetArgumentParser()
    parser.add_argument("--var_str", type=str)
    parser.add_argument("--var_int", type=int)
    parser.add_argument("--var_true", action="store_true")
    parser(main, False, 0.2, ["nap", "--port", str(port_start)])

def tcp_socket_autoformat():
    def main(args):
        if args.var_str == "damn":
            return args.var_int / 0
        return vars(args)

    parser = NetArgumentParser()
    parser.add_argument("--var_str", type=str)
    parser.add_argument("--var_int", type=int)
    parser.add_argument("--var_true", action="store_true")
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 1)])

def tcp_socket_autoformat_nargs_append():
    def main(args):
        return vars(args)

    parser = NetArgumentParser()
    parser.add_argument("-x", type=str, nargs="+")
    parser.add_argument("-y", type=str, action="append")
    parser.add_argument("-z", type=str, nargs="+", action="append")
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 2)])

def tcp_socket_no_args():
    def main(args):
        return {"a": 1}

    parser = NetArgumentParser()
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 3)])

def http_no_autoformat():
    def main(args):
        if args.var_str == "damn":
            return args.var_int / 0
        return f'"{args}"'

    parser = NetArgumentParser()
    parser.add_argument("--var_str", type=str)
    parser.add_argument("--var_int", type=int)
    parser.add_argument("--var_true", action="store_true")
    parser(main, False, 0.2, ["nap", "--port", str(port_start + 4), "--http"])

def http_autoformat():
    def main(args):
        if args.var_str == "damn":
            return args.var_int / 0
        return vars(args)

    parser = NetArgumentParser()
    parser.add_argument("--var_str", type=str)
    parser.add_argument("--var_int", type=int)
    parser.add_argument("--var_true", action="store_true")
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 5), "--http"])

def http_autoformat_nargs_append():
    def main(args):
        return vars(args)

    parser = NetArgumentParser()
    parser.add_argument("-x", type=str, nargs="+")
    parser.add_argument("-y", type=str, action="append")
    parser.add_argument("-z", type=str, nargs="+", action="append")
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 6), "--http"])

def http_no_args():
    def main(args):
        return {"a": 1}

    parser = NetArgumentParser()
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 7), "--http"])

def http_nested_dict():
    def main(args):
        return {"a": {"b": "b1", "c": {"d": "d1", "e": "e1"}, "f": "f1"}, "g": "g1"}

    parser = NetArgumentParser()
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 8), "--http"])

def http_autoformat_no_dict():
    def main(args):
        return "test"

    parser = NetArgumentParser()
    parser(main, resp_delay=0.2, parse_args=["nap", "--port", str(port_start + 9), "--http"])


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

    # Plain xml, no autoformat
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

    def test_plain_xml_na_func_exc(self):
        ans = s_tcp_na.txrx(b"<nap><__var_str>damn</__var_str><__var_int>5</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response></response><exception>division by zero</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    # Plain json, no autoformat
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

    def test_plain_json_na_func_exc(self):
        ans = s_tcp_na.txrx(b'{"--var_str": "damn", "--var_int": "5"}')
        self.assertEqual(ans, b'{"response": "", "exception": "division by zero", "finished": 1}')
        self.assertResponse(ans, "json")

    # Plain xml, autoformat
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

    def test_plain_xml_a_func_exc(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>damn</__var_str><__var_int>5</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response></response><exception>division by zero</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_whitespace_double_quote(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>\"hello world\"</__var_str><__var_int>2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response><var_str>hello world</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_whitespace_single_quote(self):
        ans = s_tcp_a.txrx(b"<nap><__var_str>'hello world'</__var_str><__var_int>2</__var_int></nap>")
        self.assertEqual(ans, b"<nap><response><var_str>hello world</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_narap_two_append(self):
        ans = s_tcp_a_narap.txrx(b"<nap><_x>1 2 3</_x><_x>11 22 33</_x><_y>1</_y><_y>11</_y><_z>1 2 3</_z><_z>11 22 33</_z></nap>")
        self.assertEqual(ans, b"<nap><response><x>['11', '22', '33']</x><y>['1', '11']</y><z>[['1', '2', '3'], ['11', '22', '33']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_narap_three_append(self):
        ans = s_tcp_a_narap.txrx(b"<nap><_x>1 2 3</_x><_x>11 22 33</_x><_x>111 222 333</_x><_y>1</_y><_y>11</_y><_y>111</_y><_z>1 2 3</_z><_z>11 22 33</_z><_z>111 222 333</_z></nap>")
        self.assertEqual(ans, b"<nap><response><x>['111', '222', '333']</x><y>['1', '11', '111']</y><z>[['1', '2', '3'], ['11', '22', '33'], ['111', '222', '333']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_narap_double_quotes(self):
        ans = s_tcp_a_narap.txrx(b'<nap><_x>"1 2" 3</_x><_y>1</_y><_y>"1 1"</_y><_y>111</_y><_z>1 "2 3"</_z><_z>"11 22" 33</_z><_z>111 "2 \'2 2" 333</_z></nap>')
        self.assertEqual(ans, b"<nap><response><x>['1 2', '3']</x><y>['1', '1 1', '111']</y><z>[['1', '2 3'], ['11 22', '33'], ['111', \"2 '2 2\", '333']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_narap_single_quotes(self):
        ans = s_tcp_a_narap.txrx(b"<nap><_x>'1 2' 3</_x><_y>1</_y><_y>'1 1'</_y><_y>111</_y><_z>1 '2 3'</_z><_z>'11 22' 33</_z><_z>111 '2 \"2 2' 333</_z></nap>")
        self.assertEqual(ans, b"<nap><response><x>['1 2', '3']</x><y>['1', '1 1', '111']</y><z>[['1', '2 3'], ['11 22', '33'], ['111', '2 \"2 2', '333']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_invalid_a_narap(self):
        ans = s_tcp_a_narap.txrx(b"<nap><_x>1 2 3</_x><_x>11 22 33</_x><_x>111 222 333</_x><_y>1 2</_y><_y>11 22</_y><_y>111 222</_y><_z>1 2 3</_z><_z>11 22 33</_z><_z>111 222 333</_z></nap>")
        self.assertEqual(ans, b"<nap><response></response><exception>unrecognized arguments: 2 22 222</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_plain_xml_a_no_arguments(self):
        ans = s_tcp_a_no_args.txrx(b"<nap></nap>")
        self.assertEqual(ans, b"<nap><response><a>1</a></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    # Plain json, autoformat
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

    def test_plain_json_a_func_exc(self):
        ans = s_tcp_a.txrx(b'{"--var_str": "damn", "--var_int": "5"}')
        self.assertEqual(ans, b'{"response": "", "exception": "division by zero", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_whitespace_single_quote(self):
        ans = s_tcp_a.txrx(b'{"--var_str": "\'hello world\'", "--var_int": "2"}')
        self.assertEqual(ans, b'{"response": {"var_str": "hello world", "var_int": 2, "var_true": false, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_narap_two_append(self):
        ans = s_tcp_a_narap.txrx(b'{"-x": ["1 2 3", "11 22 33"], "-y": [1, 11], "-z": ["1 2 3", "11 22 33"]}')
        self.assertEqual(ans, b'{"response": {"x": ["11", "22", "33"], "y": ["1", "11"], "z": [["1", "2", "3"], ["11", "22", "33"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_narap_three_append(self):
        ans = s_tcp_a_narap.txrx(b'{"-x": ["1 2 3", "11 22 33", "111 222 333"], "-y": [1, 11, 111], "-z": ["1 2 3", "11 22 33", "111 222 333"]}')
        self.assertEqual(ans, b'{"response": {"x": ["111", "222", "333"], "y": ["1", "11", "111"], "z": [["1", "2", "3"], ["11", "22", "33"], ["111", "222", "333"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_narap_double_key(self):
        ans = s_tcp_a_narap.txrx(b'{"-x": "1 2 3", "-x": "11 22 33", "-y": 1, "-y": 11, "-z": "11 22 33", "-z": "11 22 33"}')
        self.assertEqual(ans, b'{"response": {"x": ["11", "22", "33"], "y": ["11"], "z": [["11", "22", "33"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_narap_single_quotes(self):
        ans = s_tcp_a_narap.txrx(b'{"-x": ["\'11 1\' 222 333"], "-y": [1, "\'1 1\'", 111], "-z": ["1 \'2 3\'", "\'11 22\' 33", "111 \'2 \\"2 2\' 333"]}')
        self.assertEqual(ans, b'{"response": {"x": ["11 1", "222", "333"], "y": ["1", "1 1", "111"], "z": [["1", "2 3"], ["11 22", "33"], ["111", "2 \\"2 2", "333"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_invalid_a_narap(self):
        ans = s_tcp_a_narap.txrx(b'{"-x": ["1 2 3", "11 22 33"], "-y": ["1 2", "11 22"], "-z": ["1 2 3", "11 22 33"]}')
        self.assertEqual(ans, b'{"response": "", "exception": "unrecognized arguments: 2 22", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_plain_json_a_no_arguments(self):
        ans = s_tcp_a_no_args.txrx(b'{}')
        self.assertEqual(ans, b'{"response": {"a": 1}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    # HTTP, json resp, no autoformat
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

    def test_http_json_na_func_exc(self):
        ans = s_http_na.txrx("/?--var_str=damn&--var_int=5")
        self.assertEqual(ans, '{"response": "", "exception": "division by zero", "finished": 1}')
        self.assertResponse(ans, "json")

    # HTTP, xml resp, no autoformat
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

    def test_http_xml_na_func_exc(self):
        ans = s_http_na.txrx("/xml?--var_str=damn&--var_int=5")
        self.assertEqual(ans, "<nap><response></response><exception>division by zero</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    # HTTP, json resp, autoformat
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

    def test_http_json_a_func_exc(self):
        ans = s_http_a.txrx("/?--var_str=damn&--var_int=5")
        self.assertEqual(ans, '{"response": "", "exception": "division by zero", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_whitespace_double_quote(self):
        ans = s_http_a.txrx("/?--var_str=\"hello world\"&--var_int=2")
        self.assertEqual(ans, '{"response": {"var_str": "hello world", "var_int": 2, "var_true": false, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_whitespace_single_quote(self):
        ans = s_http_a.txrx("/?--var_str='hello world'&--var_int=2")
        self.assertEqual(ans, '{"response": {"var_str": "hello world", "var_int": 2, "var_true": false, "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_narap_two_append(self):
        ans = s_http_a_narap.txrx("/?-x=1 2 3&-x=11 22 33&-y=1&-y=11&-z=1 2 3&-z=11 22 33")
        self.assertEqual(ans, '{"response": {"x": ["11", "22", "33"], "y": ["1", "11"], "z": [["1", "2", "3"], ["11", "22", "33"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_narap_three_append(self):
        ans = s_http_a_narap.txrx("/?-x=1 2 3&-x=11 22 33&-x=111 222 333&-y=1&-y=11&-y=111&-z=1 2 3&-z=11 22 33&-z=111 222 333")
        self.assertEqual(ans, '{"response": {"x": ["111", "222", "333"], "y": ["1", "11", "111"], "z": [["1", "2", "3"], ["11", "22", "33"], ["111", "222", "333"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_narap_double_quotes(self):
        ans = s_http_a_narap.txrx('/?-x="11 1" 222 333&-y=1&-y="1 1"&-y=111&-z=1 "2 3"&-z="11 22" 33&-z=111 "2 \'2 2" 333')
        self.assertEqual(ans, '{"response": {"x": ["11 1", "222", "333"], "y": ["1", "1 1", "111"], "z": [["1", "2 3"], ["11 22", "33"], ["111", "2 \'2 2", "333"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_narap_single_quotes(self):
        ans = s_http_a_narap.txrx("/?-x='11 1' 222 333&-y=1&-y='1 1'&-y=111&-z=1 '2 3'&-z='11 22' 33&-z=111 '2 \"2 2' 333")
        self.assertEqual(ans, '{"response": {"x": ["11 1", "222", "333"], "y": ["1", "1 1", "111"], "z": [["1", "2 3"], ["11 22", "33"], ["111", "2 \\"2 2", "333"]], "_cmd": "nap"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_invalid_a_narap(self):
        ans = s_http_a_narap.txrx("/?-x=1 2 3&-x=11 22 33&-y=1 2&-y=11 22&-z=1 2 3&-z=11 22 33")
        self.assertEqual(ans, '{"response": "", "exception": "unrecognized arguments: 2 22", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_no_arguments(self):
        ans = s_http_a_no_args.txrx("/")
        self.assertEqual(ans, '{"response": {"a": 1}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_nested_dict(self):
        ans = s_http_a_nest_d.txrx("/")
        self.assertEqual(ans, '{"response": {"a": {"b": "b1", "c": {"d": "d1", "e": "e1"}, "f": "f1"}, "g": "g1"}, "exception": "", "finished": 1}')
        self.assertResponse(ans, "json")

    def test_http_json_a_no_dict(self):
        ans = s_http_a_no_d.txrx("/")
        self.assertEqual(ans, '{"response": "", "exception": "Cannot autoformat non-dict. Check return of the function started by NetArgumentParser.", "finished": 1}')
        self.assertResponse(ans, "json")

    # HTTP, xml resp, autoformat
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

    def test_http_xml_a_func_exc(self):
        ans = s_http_a.txrx("/xml?--var_str=damn&--var_int=5")
        self.assertEqual(ans, "<nap><response></response><exception>division by zero</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_whitespace_double_quote(self):
        ans = s_http_a.txrx("/xml?--var_str=\"hello world\"&--var_int=2")
        self.assertEqual(ans, "<nap><response><var_str>hello world</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_whitespace_single_quote(self):
        ans = s_http_a.txrx("/xml?--var_str='hello world'&--var_int=2")
        self.assertEqual(ans, "<nap><response><var_str>hello world</var_str><var_int>2</var_int><var_true>False</var_true><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_narap_double_quotes(self):
        ans = s_http_a_narap.txrx('/xml?-x="11 1" 222 333&-y=1&-y="1 1"&-y=111&-z=1 "2 3"&-z="11 22" 33&-z=111 "2 \'2 2" 333')
        self.assertEqual(ans, "<nap><response><x>['11 1', '222', '333']</x><y>['1', '1 1', '111']</y><z>[['1', '2 3'], ['11 22', '33'], ['111', \"2 '2 2\", '333']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_narap_single_quotes(self):
        ans = s_http_a_narap.txrx("/xml?-x='11 1' 222 333&-y=1&-y='1 1'&-y=111&-z=1 '2 3'&-z='11 22' 33&-z=111 '2 \"2 2' 333")
        self.assertEqual(ans, "<nap><response><x>['11 1', '222', '333']</x><y>['1', '1 1', '111']</y><z>[['1', '2 3'], ['11 22', '33'], ['111', '2 \"2 2', '333']]</z><_cmd>nap</_cmd></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_no_arguments(self):
        ans = s_http_a_no_args.txrx("/xml")
        self.assertEqual(ans, "<nap><response><a>1</a></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_nested_dict(self):
        ans = s_http_a_nest_d.txrx("/xml")
        self.assertEqual(ans, "<nap><response><a><b>b1</b><c><d>d1</d><e>e1</e></c><f>f1</f></a><g>g1</g></response><exception></exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")

    def test_http_xml_a_no_dict(self):
        ans = s_http_a_no_d.txrx("/xml")
        self.assertEqual(ans, "<nap><response></response><exception>Cannot autoformat non-dict. Check return of the function started by NetArgumentParser.</exception><finished>1</finished></nap>")
        self.assertResponse(ans, "xml")


if __name__ == "__main__":
    for t in [tcp_socket_no_autoformat, tcp_socket_autoformat, tcp_socket_autoformat_nargs_append, tcp_socket_no_args,
              http_no_autoformat, http_autoformat, http_autoformat_nargs_append, http_no_args, http_nested_dict,
              http_autoformat_no_dict]:
        Thread(target=t, daemon=True).start()

    for i in range(10):
        if i == 9:
            raise ConnectionRefusedError()
        try:
            if not "s_tcp_na" in globals():
                s_tcp_na = TcpSocketRequest(port_start)
            if not "s_tcp_a" in globals():
                s_tcp_a = TcpSocketRequest(port_start + 1)
            if not "s_tcp_a_narap" in globals():
                s_tcp_a_narap = TcpSocketRequest(port_start + 2)
            if not "s_tcp_a_no_args" in globals():
                s_tcp_a_no_args = TcpSocketRequest(port_start + 3)
            if not "s_http_na" in globals():
                s_http_na = HttpRequest(port_start + 4)
            if not "s_http_a" in globals():
                s_http_a = HttpRequest(port_start + 5)
            if not "s_http_a_narap" in globals():
                s_http_a_narap = HttpRequest(port_start + 6)
            if not "s_http_a_no_args" in globals():
                s_http_a_no_args = HttpRequest(port_start + 7)
            if not "s_http_a_nest_d" in globals():
                s_http_a_nest_d = HttpRequest(port_start + 8)
            if not "s_http_a_no_d" in globals():
                s_http_a_no_d = HttpRequest(port_start + 9)
            break
        except (ConnectionRefusedError, requests.exceptions.ConnectionError):
            time.sleep(1)

    unittest.main()
