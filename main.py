import sys
import os
import logging

from Broker.settings import ApplicationSettings
from Broker.app import Application


logging.basicConfig(
    stream=sys.stdout,
    level=logging.DEBUG
)


logger = logging.getLogger("Launcher")

if os.path.isfile(os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')):
    logger.info("settings.json File Found")
    import json
    json_data: dict = json.load(open('settings.json'))
else:
    logging.info("No JSON File Found. Loading Settings from Environment Variables")
    json_data: None = None


application: Application = Application(ApplicationSettings(data=json_data))


if __name__ == "__main__":
    logger.info("Starting Application")
    application.start()


