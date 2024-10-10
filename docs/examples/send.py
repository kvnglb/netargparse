import argparse
import socket


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, required=True)
parser.add_argument("--xml", action="store_true")
args = parser.parse_args()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", args.port))

if args.xml:
    s.sendall(b"<nap><_x>one</_x><_y>2</_y></nap>")
else:
    s.sendall(b'{"-x": "one", "-y": "1"}')

print("received:", s.recv(256).decode("utf-8"))
