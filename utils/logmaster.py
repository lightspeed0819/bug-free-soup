import logging
from datetime import datetime

_CURR_SESSION_LOG = "logs/" + str(datetime.now().strftime("%H-%M-%S")) + ".log"

logging.basicConfig(
    filename=_CURR_SESSION_LOG,
    filemode='a',
    format="%(asctime)s: %(levelname)s: %(filename)s: %(funcName)s: %(message)s",
    level=logging.DEBUG
)

def getLogger():
    return logging.getLogger(__name__)
