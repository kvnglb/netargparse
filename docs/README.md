# CLI commands
The script using NetArgumentParser can be run in two modes
- Standalone (also called main): `python <file> main <arg> <val> <arg1> <val1> ...`
  The script just behaves like it would when using the ArgumentParser of the standard library argparse.
- API (also called nap): `python <file> nap [-h] [-i IP] -p PORT [--http]` with
  ```
  -h, --help            show this help message and exit
  -i IP, --ip IP        IP address where NetArgumentParser listens. Default is 127.0.0.1.
  -p PORT, --port PORT  Port number where NetArgumentParser listens.
  --http                Use http get requests instead of plain tcp messages.
  ```
  The script starts listening on a port and waits for a TCP connection to be established. Then, the arguments for the script can be sent either with an HTTP get request or a plain TCP message.

The standalone mode does not really differ from the default behaviour of the standard ArgumentParser. The following sections therefore only apply to the API mode, unless otherwise stated.

# Sections in the response
- Standalone: The return of the script is ignored.
- API: There are three sections in the response:
  - **Response**: Everything the script returns
  - **Exception**: If something goes wrong, the message of the exception
  - **Finished**: Always `1` to indicate, that the script is done; no matter whether it had failed or not

# Message types
netargparse supports either plain TCP messages or, if the `--http` switch is passed, HTTP get requests. The supported formats for both are json and xml.

## HTTP
The arguments must be given as url parameters. The return is json (when sending to `<address>:<port>/`) or xml (when sending to `<address>:<port>/xml`).
examples:
- `http://localhost/?<arg>=<val>&<arg1>=<val1>&...` -> `{"response": {"<ret>": <val>, "<ret1>": <val1>, ...}, "exception": "", "finished": 1}`
- `http://localhost/xml?<arg>=<val>&<arg1>=<val1>&...` -> `<nap><response><ret>val</ret><ret1>val1</ret1>...</response><exception></exception><finished>1</finished></nap>`

## plain TCP
netargparse answers in the same format as the received message with the arguments. Sending just a valid json string will also return a (valid)¹ json string, same for xml. The two files in the examples directory of the docs show what the messages should look like when using plain tcp communication. Running the script with the API with `python docs/examples/main.py nap -p 7000` and in another shell either `python docs/examples/send.py -p 7000` or `python docs/examples/send.py -p 7000 --xml` will display the return of main.py.

¹ Can also be invalid, depending on what the main function returns.

# Script requirements
The Python script that uses the NetArgumentParser must follow these rules:
1)  - One main function, that is called from the NetArgumentParser
    - The main function must take only one argument of type argparse.Namespace

    file: `example1.py`
    ```python
    from netargparse import NetArgumentParser

    def add(x, y):
        return x + y

    def main(args):
        s = add(args.x, args.y)
        print(s)
        return {}

    parser = NetArgumentParser()
    parser.add_argument("-x", type=int, required=True)
    parser.add_argument("-y", type=int, required=True)
    parser(main)
    ```
    Running the script as standalone with `python example1.py main -x 5 -y 5` will display the number `10` in the CLI. Running the script with the API `python example1.py nap -p 7000 --http`, the script is able to accept its arguments from a HTTP get request, that has the arguments for the script as url parameters. So visiting http://localhost:7000/?-x=5&-y=5 will do the same: `10` in the terminal, where the script was started. The return of the HTTP get request is a json string `{"response": {}, "exception": "", "finished": 1}`. There is just an empty dictionary in the response because the script adds no entries (at least `return {}` must be returned when `autoformat=True` (default) is used, see below for further details).

2)  To receive a valid response, there are two possibilities
    - NetArgumentParser takes care of a valid format in the response section (default `autoformat=True`). The main function must return a dictionary, and its entries will be either converted into a valid json or xml string. The dictionary MUST contain only values of type
      - dictionary,
      - string or
      - any other non-dictionary/non-iterable, that is convertible to string and json serializable

      Of course, the values in the dictionary don't have to be of the same type. These rules apply recursively to all nested dictionaries. 

      file: `example2.py`
      ```python
      from netargparse import NetArgumentParser

      def main(args):
          s = args.x + args.y
          return {"sum": s}

      parser = NetArgumentParser()
      parser.add_argument("-x", type=int, required=True)
      parser.add_argument("-y", type=int, required=True)
      parser(main)
      ````
      Running the script as above will return `{"response": {"sum": 10}, "exception": "", "finished": 1}` or `<nap><response><sum>10</sum></response><exception></exception><finished>1</finished></nap>`

    - The function itself is responsible for a valid format in the response section (`autoformat=False`). The main function must return a string, that can be anything. The function is responsible for giving a valid json or xml format but can also just send unformatted stuff, where the receiver of this message will have hard times interpreting this message.

      file: `example3.py`
      ```python
      from netargparse import NetArgumentParser

      def main(args):
          s = args.x + args.y
          return f'Some weird <xml> {{"stuff": {s}"'

      parser = NetArgumentParser()
      parser.add_argument("-x", type=int, required=True)
      parser.add_argument("-y", type=int, required=True)
      parser(main, autoformat=False)
      ````
      Running the script as above either returns `{"response": Some weird <xml> {"stuff": 10", "exception": "", "finished": 1}` or `<nap><response>Some weird <xml> {"stuff": 10"</response><exception></exception><finished>1</finished></nap>`.

3)  A parser argument with the destination of `_cmd` is not allowed, because it is added by the NetArgumentParser to determine whether the main function is executed as standalone or in API mode.

    file: `example4.py`
    ```python
    from netargparse import NetArgumentParser

    def main(args):
        s = args.x + args.y
        if args._cmd == "main":
            print(s)
        else:
            return {"sum": s}

    parser = NetArgumentParser()
    parser.add_argument("-x", type=int, required=True)
    parser.add_argument("-y", type=int, required=True)
    parser(main)
    ````
    When running the script in standalone, it will print the sum in the terminal, whereas in API mode, the terminal stays clean and the return of the main function is just send to the client.

4)  The script using NetArgumentParser must not have arguments with leading underscore.

    NetArgumentParser replaces leading underscores in receiving xml messages with dashes, e.g. `__x=5` will become `--x=5`. This is because `<nap><--x>5</--x></nap>` is invalid xml syntax but `<nap><__x>5</__x></nap>` is valid. So to pass the argument `--x=5` with xml, a substitution of the leading dashes is required. If the script really needs the argument `-_x=5`... Just don't, because sending `<nap><-_x>5</-_x></nap>` is not possible and `<nap><__x>5</__x></nap>` will result in `--x=5`.

5) Arguments with `nargs="+"` and/or `action="append"` are handled as shown in the table below. Examples can be found in [examples/nargs_append](examples/nargs_append). Strings with whitespaces in between, that should be handled as one argument, must be enclosed in `"` or `'`.

   |main \ nap|url parameters|json|xml|
   |--|--|--|--|
   |`-x 1 2 3`|`?-x=1 2 3`|`{"-x": "1 2 3"}`|`<nap><_x>1 2 3</_x></nap>`|
   |`-x 1 -x 2 -x 3`|`?-x=1&-x=2&-x=3`|`{"-x": [1, 2, 3]}`|`<nap><_x>1</_x><_x>2</_x><_x>3</_x></nap>`|
   |`-x 1 2 3 -x 11 22 33 -x 111 222 333`|`?-x=1 2 3&-x=11 22 33&-x=111 222 333`|`{"-x": ["1 2 3", "11 22 33", "111 222 333"]}`|`<nap><_x>1 2 3</_x><_x>11 22 33</_x><_x>111 222 333</_x></nap>`|
   |`-x "hello world"`|`?-x="hello world"`|`{"-x": ["'hello world'"]}`|`<nap><_x>"hello world"</_x></nap>`|

   NOTE:
     - Having the same tag multiple times in xml is fine, but having two identical keys in json will drop the first entry. So `{"a": 1, "a": 2}'` will result in `{'a': 2}`.
     - Depending on the software that sends the HTTP request with the url parameters, the special characters may need to be replaced, e.g. whitespace with `%20`. So `?-x=1 2 3` will become `?-x=1%202%203`.
