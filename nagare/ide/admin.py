#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Section of Nagare administrative interface"""

from __future__ import with_statement

from nagare import presentation

class Admin(object):
    priority = 1000

    def __init__(self, apps):
        """Initialization

        In:
          - ``apps`` -- list of tuples (application, application name, application urls)
        """
        # Find the url of the ``nagare.ide`` application
        self.ide_url = [urls[0] for (app, _, urls) in apps if app.project_name == 'nagare.ide']

@presentation.render_for(Admin)
def render(self, h, *args):
    if self.ide_url:
        with h.div:
            h << h.h2('Developer tools')
            h << h.a('Switch to the IDE', href='/'+self.ide_url[0], target='nagare_ide_window')

    return h.root
