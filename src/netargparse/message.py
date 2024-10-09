import json
import typing as t
import xml.etree.ElementTree as ElementTree


class Message:
    """Meta message handler class.

    This class can be used instead of `MessageXml` or `MessageJson`, when it is
    not known, which type of message is received. Automatically detect
    the type of the message and then behave like `MessageXml` or `MessageJson`.

    Attributes
    ----------
    msg_meth : MessageXml | MessageJson
        The message method, which `Message` should behave like.

    """

    def __init__(self, msg: bytes) -> None:
        """Determine which type of message is received.

        Parameters
        ----------
        msg
            Depending on the content of msg, either set `msg_meth`
            to an instance of `MessageXml` or `MessageJson`

        Raises
        ------
        Exception
            When the received message is in an unknown format or does not
            fullfill the needs for the xml or json message.

        """
        if msg.strip().startswith(b"<nap>"):
            self.msg_meth = MessageXml()  # type: t.Union[MessageXml, MessageJson]
        elif msg.strip().startswith(b"{"):
            self.msg_meth = MessageJson()
        else:
            raise Exception("Received unknown message format.")

    def __getattr__(self, name: str) -> t.Any:
        """Make this class behave like `MessageXml` or `MessageJson`.

        Parameters
        ----------
        name
            Name of the function, that should be called from `MessageXml` or
            `MessageJson`.

        Returns
        -------
        Return what the function of the composed class return.

        """
        return getattr(self.msg_meth, name)

    @staticmethod
    def dict_to_argstring(d: dict) -> str:
        """Convert the dict with the main `parser` arguments into a str.

        The function `parser.parse_args` needs a list as input with the arguments
        as input, but the received message from the client is converted into a
        dict. So this function converts the dict into a str, that can be splitted
        at a whitespace character, to get a list with the arguments for the `parser`.

        Additionally, clean the arguments. E.g. an argument can be `--x 1`, but
        xml syntax forbids `<--x>1</--x>`. To overcome this, underscore instead
        of dash can be used: `<__x>1</__x>`.

        ANNOTATION: DO NOT USE ARGUMENTS FOR THE MAIN PARSER THAT START WITH
                    UNDERSCORE, BECAUSE THEY WILL BE CONVERTED INTO DASH.

        Parameters
        ----------
        d
            Dirty arguments for the main `parser`.

        Returns
        -------
        Clean Arguments for the `main` parser (splittable at whitespace).

        """
        lst = []
        for key, value in d.items():
            k = key.lstrip("_")
            dash = "-" * (len(key) - len(k))
            k = dash + k
            if value:
                lst.append(f"{k} {value}")
            else:
                lst.append(k)
        return " ".join(lst)


class MessageXml:
    """Handle xml messages."""

    @staticmethod
    def _to_dict(xml: t.Union[bytes, str]) -> dict:
        """Convert bytes / a string with xml syntax into a dict.

        Parameters
        ----------
        xml
            The xml formatted bytes/string.

        Raises
        ------
        Exception
            Root element of xml must be <nap>.

        Returns
        -------
        A dict with the keys of the xml tags and its texts as values.

        """
        root = ElementTree.fromstring(xml)

        if root.tag != "nap":
            raise Exception("Root must be named `nap`. Message must be in `<nap>...</nap>`.")

        ret = {}
        for child in root:
            ret[child.tag] = child.text
        return ret

    @staticmethod
    def _from_dict(d: dict) -> str:
        """Convert a dict into xml formatted str.

        Parameters
        ----------
        d
            Dictionary, that should be converted an xml styled str.

        Returns
        -------
        The xml styled str with tags of the dict keys and its values as texts.

        """
        root = ElementTree.Element("root")
        for key, val in d.items():
            ElementTree.SubElement(root, key).text = str(val)
        return "".join(ElementTree.tostring(e, encoding="unicode") for e in root)

    @staticmethod
    def _replace_breaking_chars(string: str) -> str:
        """Replace xml breaking characters with xml unbreaking characters."""
        return string.replace("<", "[").replace(">", "]")

    @staticmethod
    def _end_of_msg(string: bytes) -> bool:
        """Determine, if the received message is complete.

        The message from the client is received in chunks, and to determine
        whether the message is complete, this function checks if the root
        element of the xml message is closed.

        Parameters
        ----------
        string
            The message, that was received by the client so far.

        Returns
        -------
        Whether the message is fully received.

        """
        return string.strip().endswith(b"</nap>")

    def _format(self, autoformat: bool, resp: t.Union[dict, str], exc: str) -> bytes:
        """Format the message to be sent to the client.

        Parameters
        ----------
        autoformat
            True: resp must be a dict and is converted into xml string, where
                  the keys of the dict will be xml tags and the values of the
                  dict will be the xml texts.
            False: resp will be sent to the client "as is".
        resp
            The information that should be sent in the response section.
        exc
            The information that should be sent in the exception section.

        Raises
        ------
        Exception
            When autoformat is true but the function `func` does not
            return a dict.

        Returns
        -------
        Message that is sent to the client.

        """
        e = self._replace_breaking_chars(exc)
        if resp == "":
            r = resp
        else:
            if autoformat and isinstance(resp, dict):
                r = self._from_dict(resp)
            elif autoformat and not isinstance(resp, dict):
                raise Exception("Cannot autoformat string. Check return of the function started by NetArgumentParser.")
            else:
                r = resp
        return "<nap><response>{}</response><exception>{}</exception><finished>1</finished></nap>".format(r, e).encode("utf-8")


class MessageJson:
    """Handle json messages."""

    @staticmethod
    def _to_dict(json_string: t.Union[bytes, str]) -> dict:
        """Convert bytes / a string with json syntax into a dict.

        Parameters
        ----------
        json_string
            The json formatted bytes/string.

        Returns
        -------
        A dict with the keys of the json keys and its values.

        """
        return json.loads(json_string)

    @staticmethod
    def _from_dict(d: t.Union[dict, str]) -> str:
        """Convert a dict into a json formatted str.

        Parameters
        ----------
        d
            Dictionary, that should be converted a json styled str. A str will
            be also formatted in a valid json string.

        Returns
        -------
        The json styled str with keys of the dict keys and its values.

        """
        return json.dumps(d)

    @staticmethod
    def _replace_breaking_chars(string: str) -> str:
        """Replace json breaking characters with json unbreaking characters."""
        return string.replace('"', "'")

    @staticmethod
    def _end_of_msg(string: bytes) -> bool:
        """Determine, if the received message is complete.

        The message from the client is received in chunks, and to determine
        whether the message is complete, this function checks if the number of
        opening `{` equals the number of closed `}`.

        ANNOTATION: DO NOT SEND STRING ARGUMENTS WITH INCOMPLETE
                    CURLY PARENTHESES.

        Parameters
        ----------
        string
            The message, that was received by the client so far.

        Returns
        -------
        Whether the message is fully received.

        """
        return string.count(b"{") == string.count(b"}")

    def _format(self, autoformat: bool, resp: t.Union[dict, str], exc: str) -> bytes:
        """Format the message to be sent to the client.

        Parameters
        ----------
        autoformat
            True: resp is converted into a json string, where the keys of the
                  dict will be json keys and the values of the dict will be
                  the json keys texts. A plain str is autoformatted into a
                  valid json str.
            False: resp will be sent to the client "as is".
        resp
            The information that should be sent in the response section.
        exc
            The information that should be sent in the exception section.

        Returns
        -------
        Message that is sent to the client.

        """
        e = self._replace_breaking_chars(exc)
        if resp == "":
            r = resp
            ret = '{{"response": "{}", "exception": "{}", "finished": 1}}'
        else:
            r = self._from_dict(resp) if autoformat else resp
            ret = '{{"response": {}, "exception": "{}", "finished": 1}}'
        return ret.format(r, e).encode("utf-8")
