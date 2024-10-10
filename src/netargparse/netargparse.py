import argparse
import time
import typing as t

from .server import HttpServer, TcpSocketServer


class ArgumentParserNoExit(argparse.ArgumentParser):
    """Make the class `ArgumentParser` not exit on error."""

    def error(self, msg: str) -> t.NoReturn:
        """Overwrite `error` to raise an exception instead of also exiting."""
        raise Exception(msg)


class NetArgumentParser:
    """The class that should be the drop-in replacement for `ArgumentParser`.

    Attributes
    ----------
    meta_parser : ArgumentParserNoExit
        The parser, that contains two subparsers, to determine whether the script,
        that uses this library, runs as standalone (function arguments passed by cli) or
        network argument parser (function arguments passed by tcp message).
    parser : ArgumentParserNoExit
        The pendant to `parser = argparse.ArgumentParser()` but at level 1 (subparser)
        instead of level 0.
    args : argparse.Namespace
        The arguments from the `meta_parser`. Either containing the arguments, that
        are required for the function or the arguments to run the tcp server.

    """

    def __init__(self) -> None:
        """Initialize the `meta_parser` and `parser` and configure the `nap_parser`."""
        self.meta_parser = ArgumentParserNoExit()

        subparser = self.meta_parser.add_subparsers(dest="_cmd")

        nap_parser = subparser.add_parser("nap")
        nap_parser.add_argument("-i", "--ip", type=str, required=False, default="127.0.0.1",
                                help="IP address where NetArgumentParser listens. Default is localhost.")
        nap_parser.add_argument("-p", "--port", type=int, required=True,
                                help="Port number where NetArgumentParser listens.")
        nap_parser.add_argument("--http", action="store_true",
                                help="Use http get requests instead of plain tcp messages (requires flask).")

        self.parser = subparser.add_parser("main")

    def __call__(self, func: t.Callable,
                 autoformat: bool = True,
                 resp_delay: t.Union[int, float] = 0,
                 parse_args: t.Union[None, t.List[str]] = None) -> None:
        """Run the function `func` either directly from the cli or with nap.

        The function `func` is either executed directly or runs as tcp server
        and accepts arguments from tcp clients.

        Parameters
        ----------
        func
            THE function.
        autoformat
            True: The return of the function `func` can be a dict or str and is
                  automatically formatted to a valid xml or json format as response
                  in nap mode.
            False: The return of the function `func` is handed "as is" as response
                   in nap mode. The function `func` is required to form a valid
                   response.
        resp_delay
            Wait `resp_delay` in seconds before sending the response (return of
            `func`) in nap mode.
        parse_args
            None: Parse the arguments from the cli.
            List[str]: Parse the arguments from the list.

        """
        self.parse_args(parse_args)

        if self.args._cmd == "main":
            func(self.args)
            return

        if self.args.http:
            server = HttpServer(self.args.ip, self.args.port)  # type: t.Union[HttpServer, TcpSocketServer]
        else:
            server = TcpSocketServer(self.args.ip, self.args.port)

        while True:
            ans = ""  # type: t.Union[str, dict]
            exc = ""

            try:
                args_s = server.get_msg()
                if args_s is False:  # can also be `""`, so no `not args_s`
                    continue
                args_d = self.parser.parse_args(args_s.split(" "))
                args_d._cmd = "nap"
                ans = func(args_d)
            except Exception as e:
                exc = str(e)

            time.sleep(resp_delay)
            server.send_msg(autoformat, response=ans, exception=exc)

    def parse_args(self, parse_args: t.Union[None, t.List[str]]) -> None:
        """Prase the arguments of the `meta_parser`.

        Parameters
        ----------
        parse_args
            None: Parse the arguments from the cli.
            List[str]: Parse the arguments from the list.

        Raises
        ------
        Exception
            When not specified if the script, that is using this lib, should run
            as standalone (`main`) or tcp server (`nap`).

        """
        self.args = self.meta_parser.parse_args(parse_args)

        if self.args._cmd not in ["main", "nap"]:
            raise Exception("Either `main` or `nap` must be passed as positional argument.")
