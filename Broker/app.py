"""
Broker Application Implementation
This will connect to the Core server and retrieve configuration.
"""
import logging
import threading
import json
import websocket

from time import sleep

from Broker.broker import BrokerServer
from Broker.settings import ApplicationSettings


logger = logging.getLogger("Application")


class Application:

    def __init__(self, settings: ApplicationSettings):
        self.running = False
        self.keep_running = True

        self.broker = None
        self.broker_settings = None
        self.broker_thread = None

        self.incoming_actions = []
        self.server_updates = []

        self.ws_url = settings.websocket_url
        self.uuid = settings.uuid
        self.token = settings.token

        websocket.enableTrace(True)
        self.ws = websocket.WebSocketApp(
            self.ws_url,
            header=[
                'AUTH-UUID: {}'.format(self.uuid),
                'AUTH-TOKEN: {}'.format(self.token),
                'AUTH-TYPE: broker',
            ],
            on_close=self._on_close,
            on_message=self._on_message,
            on_error=self._on_error,
        )
        self.ws.on_open = self._on_open

        logger.info("Application Init Completed")

    @property
    def callbacks(self):
        return {
            'update_server_list': self.update_server_list
        }

    def _on_open(self):
        self.broker_thread = threading.Thread(name='BrokerTCP', target=self._broker_thread)
        self.broker_thread.start()

    def _on_message(self, event):
        data = json.loads(event)
        logger.debug("Message Received {}".format(data))
        if data.get('type') and hasattr(self, "recv_{}".format(data['type'])):
            getattr(self, "recv_{}".format(data['type']))(data)
        elif data.get('type'):
            logger.error("Invalid Action {}".format(data['type']))
        else:
            logger.error("Unparsed Message")

    def _on_error(self, event):
        ...

    def _on_close(self):
        ...

    def start(self, *args, **kwargs):
        logger.info("Running Websocket Main Loop")
        self.ws.run_forever(*args, **kwargs)
        logger.info("Stop Signal Received, or WS Run End Unexpected")
        self.stop()

    def stop(self):
        self.keep_running = False
        self.broker.stop()

    def _broker_thread(self):
        logger.info("Broker Thread Started")
        logger.info("Waiting Settings from Websocket Server")

        while not self.broker_settings and self.keep_running:
            sleep(0.5)

        if not self.keep_running:
            logger.error("Cannot Start Broker because Keep running was set to False")
            return None

        self.broker = BrokerServer(self.broker_settings, self.callbacks)

        self.broker.listen()

    def recv_update_info(self, event):
        if event.get('broker'):
            self.broker_settings = event['broker']
        else:
            logger.error("Update Info Not Related")

    def recv_server_list(self, event):
        self.server_updates.append(event['servers'])

    def update_server_list(self):
        self.ws.send(data=json.dumps({
            'type': 'update_server_list'
        }))

        logging.info("Waiting Updated Server List")

        while not self.server_updates and self.keep_running:
            sleep(0.5)

        if not self.keep_running:
            raise BrokenPipeError("Application Stop Before Sending Updated Server List")

        return self.server_updates.pop()



