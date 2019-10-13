# This file allow this module to be run as follow:
# python -m Broker

# Created for testing purposes
# Maybe it can be used in future if this project its added to PyPip

import sys
import logging
import threading

from Broker.settings import ServerSettings
from Broker import BrokerServer

logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG
)

test_server_list = [
    ServerSettings({
        "name": "Python Emulator",
        "description": "Avatar ON",
        "address": "127.0.0.1",
        "port": 8370,
        "utilization": 0,
        "capacity": 20,
        "enabled": True
    })
]

bind_address = "127.0.0.1"
bind_port = 8372

broker_server = BrokerServer({'host': bind_address, 'port': bind_port})
broker_server.server_list = test_server_list
broker_process = threading.Thread(target=broker_server.listen)

logging.info("Starting Broker Server")
broker_process.start()

try:
    while broker_process.is_alive():
        pass
except KeyboardInterrupt:
    logging.error("Keyboard Interrupt. Terminating Process")
    broker_server.stop()
    broker_process.join()
except:
    logging.exception("Uncaught Exception Found. Terminating Process", exc_info=True)
    broker_server.stop()
    broker_process.join()



