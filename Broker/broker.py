# This file is based on broker.py from gunbound-server-link
# New comments should start with your username and : (Example: Mango: Here is my comment)

import socket
import threading

import logging  # Mango: Removing all the "print" calls and changing it to logging

from typing import Union, Dict

from Broker.utils import *
from Broker.settings import BrokerSettings, ServerSettings


logger = logging.getLogger("BrokerServer")  # Creating a logger with name, this make logs more readable


class BrokerServer(object):
    # server_list = []
    server_list: list = []  # Mango: Changed Name to Server List
    # world_session = []  # Mango: Removing the shared list

    stop_listening: bool = False
    sock_timeout: int = 10  #
    """
    Mango: Adding a timeout to allow exiting thread. 
    If this broke something, instead of a thread, multiproccesing will be used.
    Right now im testing this, because multiprocessing wont attach the same logger as the main thread
    and that suck for develop. 
    """

    # def __init__(self, host, port, server_list, in_world_session): # Mango: removing the shared world_session list.
    def __init__(self, settings: Union[BrokerSettings or dict], callbacks: Dict[str, callable]):
        """
        Mango: the world session list was shared with the game server in the original version of the files.
        It was used only to calculate the users in the server. But, being shared means that every game server should
        use it, making impossible to have multiples GameServer around the world connected.
        I remove the world_session list, and right now im hard-coding the users calculation, until all the
        core channels are implemented. In that moment, the users length will be calculated Core-Server side
        """
        self.callbacks = callbacks

        if type(settings) is dict:
            settings = BrokerSettings(settings)

        if settings.socket_timeout and type(settings.socket_timeout) is int:
            self.sock_timeout = settings.socket_timeout
        elif settings.socket_timeout:
            logging.error("Invalid Timeout Data Type: [{}]. Expected int".format(type(settings.socket_timeout)))

        self.host = settings.host
        self.port = settings.port

        self.update_server_list(settings.server_list)

        # self.world_session = in_world_session Mango: Removing the shared list
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.settimeout(self.sock_timeout)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.sock.bind((self.host, self.port))
        logger.info("GunBound TCP Broker Init")
        # Mango: Removing the Server List Load from Init. The list will be loaded and updated from websocket.
        # for server_option in self.server_list:
        #     logger.info("Server: [{}] [{}] on IP:{}".format(
        #         server_option.server_name, server_option.server_description, server_option.server_port))

    def update_server_list(self, server_list):
        logger.info("Updating Server List")
        logger.debug(server_list)

        self.server_list = []

        for server in server_list:
            logging.debug("Appending Server {}".format(server['name']))
            self.server_list.append(ServerSettings(server))

        for index, server in enumerate(self.server_list):
            logger.info("Server #{}: [{}] {}:{}".format(index, server.server_name, server.server_address, server.server_port))

    def stop(self):
        """
        Mango: Adding Stop Order
        :return: None
        """
        self.stop_listening = True

    def listen(self):
        self.sock.listen(5)
        logger.info("Listening on {}:{}".format(self.host, self.port))

        while not self.stop_listening:
            try:
                client, address = self.sock.accept()
                client.settimeout(6000)
                threading.Thread(target=self.client_connection, args=(client, address)).start()
            except socket.timeout:
                pass
            except:
                logger.exception("Uncaught Exception", exc_info=True)

        logger.info("Exiting Due to Stop Signal")

    def client_connection(self, client, address):
        logger.info("New connection from {}".format(address))
        socket_rx_size = 1024
        # This value should be used during calculation of the sequence bytes
        socket_rx_sum = 0

        while True:
            try:
                data = client.recv(socket_rx_size)
                if data:
                    if len(data) < 6:
                        logger.info("Invalid Packet (length < 6)")
                        logger.info(data)
                    else:
                        # Try parse basic packet information
                        payload_size = (data[1] << 8) | data[0]
                        client_command = (data[5] << 8) | data[4]

                        logger.info("")
                        socket_rx_sum += payload_size

                        # Reply client if the service request is recognized
                        if client_command == 0x1013:
                            logger.info("Authentication Request")
                            login_packet = BrokerServer.generate_packet(-1, 0x1312,
                                                                        int_to_bytes(0x0000, 2, big_endian=True))
                            client.send(login_packet)

                        elif client_command == 0x1100:
                            logger.info("Server Directory Request")

                            server_list = self.callbacks['update_server_list']()
                            self.update_server_list(server_list)

                            directory_packet = bytearray()
                            directory_packet.extend([0x00, 0x00, 0x01])  # unknown
                            directory_packet.append(len(self.server_list))

                            for i in range(len(self.server_list)):
                                # ORIGINAL COMMENT:
                                # hack: assumes that we only use one world.
                                # For multiple worlds, tag id in the Session class
                                # self.server_list[i].server_utilization = len(self.world_session)
                                # Mango: Hard-coding the length for now
                                self.server_list[i].server_utilization = 10
                                directory_packet.extend(BrokerServer.get_individual_server(self.server_list[i], i))

                            directory_packet = BrokerServer.generate_packet(0, 0x1102, directory_packet)
                            client.send(directory_packet)

                else:
                    logger.info("Client disconnected")
                    return True
            except:
                client.close()
                logger.error("Client forcibly closed without cleanup")
                return False

    @staticmethod
    def generate_packet(sent_packet_length, command, data_bytes):
        packet_expected_length = len(data_bytes) + 6
        packet_sequence = get_sequence(sent_packet_length + packet_expected_length)

        # broker-specific: first packet of connection uses a different sequence
        if sent_packet_length == -1:
            packet_sequence = 0xCBEB

        response = bytearray()
        response.extend(int_to_bytes(packet_expected_length, 2))
        response.extend(int_to_bytes(packet_sequence, 2))
        response.extend(int_to_bytes(command, 2))

        response.extend(data_bytes)
        return response

    @staticmethod
    def get_individual_server(entry: ServerSettings, position):
        extended_description = entry.server_description + \
                               "\r\n[" + str(entry.server_utilization) + \
                               "/" + str(entry.server_capacity) + "] players online"
        response = bytearray()
        response.extend([position, 0x00, 0x00])
        response.append(len(entry.server_name))
        response.extend(entry.server_name.encode("ascii"))
        response.append(len(extended_description))
        response.extend(extended_description.encode("ascii"))
        response.extend(map(int, entry.server_address.split('.')))
        response.extend(int_to_bytes(entry.server_port, 2, big_endian=True))
        response.extend(int_to_bytes(entry.server_utilization, 2,  big_endian=True))
        response.extend(int_to_bytes(entry.server_utilization, 2,  big_endian=True))
        response.extend(int_to_bytes(entry.server_capacity, 2,  big_endian=True))
        response.append(int(entry.server_enabled))
        return response
