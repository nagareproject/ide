#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Dedicated IDE logger"""

import logging

from nagare import ajax, comet
from nagare.ide import CHANNEL_ID

class NagareHandler(logging.Handler):
    """Logger using a push channel to send the record to the IDE"""
    def emit(self, record):
        record.msg = record.msg.replace('"', r'\"')

        comet.channels.send(CHANNEL_ID, "add_log(%s);" % ajax.py2js(self.format(record)))

# Hack for Python 2.5: before v2.6, the handler classes had to be defined
# in the logging namespace
logging.NagareIdeHandler = NagareHandler
