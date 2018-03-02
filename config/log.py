import sys
import logging
from django.conf import settings


"""Default logger should be visible"""
debug_level = logging.DEBUG if settings.SYS_DEBUG else logging.INFO
root = logging.getLogger()
root.setLevel(debug_level)
ch = logging.StreamHandler(sys.stdout)
ch.setLevel(debug_level)
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
ch.setFormatter(formatter)
root.addHandler(ch)


"""Application logger"""
logger = logging.getLogger('mapemall')

logger.setLevel(logging.DEBUG)
