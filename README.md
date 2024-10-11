# netargparse
A Python library that imbues the standard ArgumentParser with an API for the Python script.

This library is intended as a replacement for the ArgumentParser of the standard argparse library, providing an additional TCP based API for handling the arguments of the script.

A minimal example `minimal.py` with the ArgumentParser could be
```
from argparse import ArgumentParser

def add_one(args):
    new_number = args.x + 1
    print(new_number)
    return(new_number)

parser = ArgumentParser()
parser.add_argument("-x", type=int, required=True)
args = parser.parse_args()
add_one(args)
```

and running the script results in
```
$ python minimal.py -x 5
6
```

Replacing the ArgumentParser with the NetArgumentParser from this library:
```
from netargparse import NetArgumentParser

def add_one(args):
    new_number = args.x + 1
    print(new_number)
    return(new_number)

nap = NetArgumentParser()
nap.parser.add_argument("-x", type=int, required=True)
nap(add_one)
```

The script can now be run in two modes:
- `main` - standalone, same behaviour as above
- `nap` - enable the API

### Main
All arguments must be passed from the CLI after the `main` argument.
```
$ python minimal.py main -x 5
6
```

### Nap
`nap` makes the script listen on a port and wait for the arguments.
```
$ python minimal.py nap --port 7000 --http
```
It is then possible to run the main function of the script by sending an HTTP get request with url parameters as arguments.

For example visit http://localhost:7000/?&-x=5 with a browser and receive the script's return as json.
```
{"response": 6, "exception": "", "finished": 1}
```

The following arguments are accepted for the `nap` mode
```
$ python minimal.py nap --help
usage: minimal.py nap [-h] [-i IP] -p PORT [--http]

optional arguments:
  -h, --help            show this help message and exit
  -i IP, --ip IP        IP address where NetArgumentParser listens. Default is localhost.
  -p PORT, --port PORT  Port number where NetArgumentParser listens.
  --http                Use http get requests instead of plain tcp messages (requires flask).
```

# Installation
For a minimal installation, where only plain TCP messages are used for communication, run
```
pip install netargparse
```
No additional libraries will be installed. All libraries used are part of [The Python Standard Library](https://docs.python.org/3/library/index.html).

If HTTP requests are to be used, run
```
pip install netargparse[http]
```
This will also install [flask](https://pypi.org/project/Flask/).

# Documentation
More documentation can be found in [docs](https://github.com/kvnglb/netargparse/tree/main/docs).
