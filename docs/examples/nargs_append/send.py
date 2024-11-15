import argparse
import socket


parser = argparse.ArgumentParser()
parser.add_argument("-p", "--port", type=int, required=True)
parser.add_argument("--xml", action="store_true")
args = parser.parse_args()


s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
s.connect(("127.0.0.1", args.port))

if args.xml:
    s.sendall(b"<nap><_x>1 2 3</_x><_x>11 22 33</_x><_y>1</_y><_y>11</_y><_z>1 2 3</_z><_z>11 22 33</_z></nap>")
else:
    s.sendall(b'{"-x": ["1 2 3", "11 22 33"], "-y": [1, 11], "-z": ["1 2 3", "11 22 33"]}')

print("received:", s.recv(256).decode("utf-8"))
