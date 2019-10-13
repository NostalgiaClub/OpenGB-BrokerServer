
import os
from typing import Union, Dict


class ApplicationSettings:
    """
    Application Settings. Init them with a dict of settings.
    Main.py will try to import settings.json.
    Missing variables in json file (or if no file present) will be loaded from ENV
    """
    websocket_url: str = None
    uuid: str = None
    token: str = None

    def __init__(self, data: Union[Dict[str, str], None] = None):
        if data and type(data) is dict:
            for k, v in data.items():
                setattr(self, k, v)
        for attr in self.__attrs__():
            if not getattr(self, attr):
                v = os.environ.get(attr)
                if not v:
                    raise EnvironmentError("Failed to Load \"{}\" Value from Environment".format(attr))
                setattr(self, attr, v)

    @staticmethod
    def __attrs__():
        """
        Required Settings to Work
        :return: Required Settings Sequence
        """
        return 'websocket_url', 'uuid', 'token'


class BrokerSettings:
    host: str = None
    port: int = None

    socket_timeout: int = None

    server_list: list = None

    def __init__(self, data: dict):
        self.host = data.get('host')
        self.port = data.get('port')
        self.socket_timeout = data.get('socket_timeout')
        self.server_list = data.get('server_list', [])


# Based on Original ServerOptions Class. Adapted to Work Here
class ServerSettings:
    def __init__(self, server: dict):
        self.server_name: str = server['name']
        self.server_description: str = server['description']
        self.server_address = server['address']
        self.server_port = server['port']
        self.server_utilization = server['utilization']
        self.server_capacity = server['capacity']
        self.server_enabled = server['enabled']



