#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import pkg_resources

from nagare import ajax

pkg_resources.declare_namespace('nagare.ide')

YUI_PREFIX = ajax.YUI_INTERNAL_PREFIX   # Use the YUI sources bundled with the Nagare distribution
CHANNEL_ID = '_nagare_ide_'             # Comet push channel name
