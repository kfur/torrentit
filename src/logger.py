
import logging
import logaugment
import sys


default_level = logging.INFO

def new_logger(level=default_level, torrent_name=None, user_id=None):
    logger = logging.Logger('')
    logger.setLevel(level)
    handler = logging.StreamHandler(sys.stdout)
    torrent_name_format = '|[%(torrent)s]' if torrent_name is not None else ""
    user_id_format = '|<%(id)s>' if user_id is not None else ""
    formatter = logging.Formatter("%(levelname)s|(%(asctime)s){}{}: %(message)s".format(torrent_name_format, user_id_format))
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logaugment.set(logger, torrent=None if torrent_name is None else torrent_name[:40], id=str(user_id))
    return logger

