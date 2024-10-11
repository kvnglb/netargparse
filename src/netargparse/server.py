import io
import socket
import typing as t

from .message import Message, MessageJson, MessageXml


class TcpSocketServer:
    """The script in nap mode accepts plain tcp messages without overhead.

    Attributes
    ----------
    connected : bool
        Indicate whether the socket has an active connection.
    sock : socket.socket
        The socket for the tcp server.
    conn : socket.socket
        Established connection of the client via tcp.
    addr : tuple[str, int]
        Contain the ip address and port of the connected client.
    msg_meth : None | message.Message
        The meta message class, that can handle message.MessageXml and
        message.MessageJson. Also determines the type of the message.

    """

    def __init__(self, ip: str, port: int) -> None:
        """Initialize the socket as server to accept tcp connections from clients.

        Parameters
        ----------
        ip
            The ip address, where the socket should listen.
        port
            The port, where the socket should listen.

        """
        self.connected = False
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.bind((ip, port))
        self.sock.listen(1)

    def disconnect(self) -> t.Literal[False]:
        """Tell the `TcpSocketServer` instance, that no client is connected.

        Returns
        -------
        False
            Indicate that a disconnection had taken place.

        """
        self.conn.close()
        self.connected = False
        return False

    def get_msg(self) -> t.Union[t.Literal[False], str]:
        """Receive the message that was sent from the client to the tcp server.

        Loop through the received message and wait until the client has sent
        the complete message. A break of the connection is handled in the
        exception, otherwise the received message is processed and converted
        into a valid `parser` string.

        Returns
        -------
        False: Something went wrong during receiving the message.
        str: Argument(s) for the main `parser` of `NetArgumentParser`.

        """
        if not self.connected:
            self.conn, self.addr = self.sock.accept()
            self.connected = True

        data = io.BytesIO()
        self.msg_meth = None
        try:
            while True:
                recv = self.conn.recv(256)
                if not recv:
                    return self.disconnect()

                if not self.msg_meth:
                    self.msg_meth = Message(recv)

                data.write(recv)

                if self.msg_meth._end_of_msg(data.getvalue()):
                    break

        except Exception as e:
            print(e)
            return self.disconnect()

        else:
            data_str = data.getvalue().decode("utf-8")
            d = self.msg_meth._to_dict(data_str)
            return Message.dict_to_argstring(d)

    def send_msg(self, autoformat: bool, response: t.Union[dict, str],
                 exception: str) -> None:
        """Send a message to the client.

        Parameters
        ----------
        autoformat
            True: The return of the function `func` can be a dict or str and is
                  automatically formatted to a valid xml or json format as response
                  in nap mode.
            False: The return of the function `func` is handed "as is" as response
                   in nap mode. The function `func` is required to form a valid
                   response.
        response
            The information that should be sent in the response section.
        exception
            The information that should be sent in the exception section.

        """
        try:
            if not self.msg_meth:
                raise Exception("`msg_meth` was `None` when `send_msg` was called.")
            else:
                msg = self.msg_meth._format(autoformat, response, exception)
                self.conn.sendall(msg)
        except Exception as e:
            print(e)
            self.disconnect()


class HttpServer:
    """The script in nap mode accepts http get requests with url parameters.

    The url parameters are processed and converted to the script arguments for
    the main `parser` of `NetArgumentParser`.

    Attributes
    ----------
    q_get : queue.Queue
        The queue, that sends and receives the message received by the client
        from the flask daemon thread to the main thread.
    q_send : queue.Queue
        The queue, that sends and receives the message from `NetArgumentParser`
        from the main thread to the flask daemon thread.

    """

    def __init__(self, ip: str, port: int) -> None:
        """Initialize flask as daemon thread to accept http get requests.

        Flask is started as daemon thread and the url parameters are sent
        to the main thread through queues for converting them into the argument
        string, that is needed for the main `parser`.

        Parameters
        ----------
        ip
            The ip address, where the flask should listen.
        port
            The port, where the socket should listen.

        """
        from queue import Queue
        from threading import Thread

        import flask

        self.q_get = Queue(maxsize=1)  # type: Queue
        self.q_send = Queue(maxsize=1)  # type: Queue

        def serve(q_get: Queue, q_send: Queue) -> None:
            """Daemon thread, that is running flask."""
            app = flask.Flask(__name__)

            def msg_handler(autoformat: bool, response: t.Union[dict, str],
                            exception: str,
                            message_method: t.Union[t.Type[MessageJson], t.Type[MessageXml]]) -> bytes:
                """Format the message to the client either as json or xml.

                Parameters
                ----------
                autoformat
                    True: The return of the function `func` can be a dict or str and is
                          automatically formatted to a valid xml or json format as response
                          in nap mode.
                    False: The return of the function `func` is handed "as is" as response
                           in nap mode. The function `func` is required to form a valid
                           response.
                response
                    The information that should be sent in the response section.
                exception
                    The information that should be sent in the exception section.
                message_method
                    Either MessageJson for json output or
                    MessageXml for xml output.

                Returns
                -------
                msg
                    The message as bytes (encoded utf-8), that is sent to the client.

                """
                msg_meth = message_method()
                msg = msg_meth._format(autoformat, response, exception)
                return msg

            @app.route("/")
            def http_get() -> flask.wrappers.Response:
                """Route for json response."""
                d = dict(flask.request.args)
                q_get.put(d)
                r = q_send.get()  # type: tuple[t.Any, t.Any, t.Any]
                return flask.Response(msg_handler(*r, MessageJson),
                                      mimetype="application/json")

            @app.route("/xml")
            def http_get_xml() -> flask.wrappers.Response:
                """Route for xml response."""
                d = dict(flask.request.args)
                q_get.put(d)
                r = q_send.get()  # type: tuple[t.Any, t.Any, t.Any]
                return flask.Response(msg_handler(*r, MessageXml),
                                      mimetype="application/xml")

            app.run(ip, port)

        thrd_serve = Thread(target=serve, args=(self.q_get, self.q_send), daemon=True)
        thrd_serve.start()

    def get_msg(self) -> str:
        """Receive the message that was sent from the client to the http server.

        Receive the message as dict from the daemon thread via the queue and
        return the corresponding argument string for the main `parser`.

        Returns
        -------
        Argument string for main `parser`.

        """
        d = self.q_get.get()
        return Message.dict_to_argstring(d)

    def send_msg(self, autoformat: bool, response: t.Union[dict, str],
                 exception: str) -> None:
        """Send the http get request response to the client.

        Parameters
        ----------
        autoformat
            True: The return of the function `func` can be a dict or str and is
                  automatically formatted to a valid xml or json format as response
                  in nap mode.
            False: The return of the function `func` is handed "as is" as response
                   in nap mode. The function `func` is required to form a valid
                   response.
        response
            The information that should be sent in the response section.
        exception
            The information that should be sent in the exception section.

        """
        try:
            self.q_send.put((autoformat, response, exception))
        except Exception as e:
            print(e)
