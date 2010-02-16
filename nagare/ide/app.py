#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import configobj
import traceback

import webob
from nagare import component, wsgi, config, comet

from nagare.ide import CHANNEL_ID, workspace

class WSGIApp(wsgi.WSGIApp):
    """The Nagare IDE application
    """

    spec = {
            'application' : {
                'max_nb_logs' : 'integer(default=10)',
                'nagare_sources' : 'boolean(default=False)'
            },

            'editor' : {
                'theme' : 'string(default="white")',
                'tabshowspace' : 'boolean(default=True)',
                'autoindent' : 'boolean(default=True)',
                'closepairs' : 'boolean(default=False)',
                'highlightline' : 'boolean(default=False)',
                'fontsize' : 'string(default="10")',
                'tabsize' : 'string(default="4")'
            }
           }

    def __init__(self, root_factory):
        """Initialization
        """
        super(WSGIApp, self).__init__(root_factory)

        self.max_nb_logs = 10
        self.nagare_sources = False # Nagare core sources displayed or not
        self.publisher = None
        self.editor_config = {}     # The Bespin editor configuration

    def set_config(self, config_filename, conf, error):
        """Process the configuration file

        In:
          - ``config_filename`` -- the path to the configuration file
          - ``config`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        conf = configobj.ConfigObj(conf, configspec=configobj.ConfigObj(WSGIApp.spec))
        config.validate(config_filename, conf, error)

        self.max_nb_logs = conf['application']['max_nb_logs']
        self.nagare_sources = conf['application']['nagare_sources']
        self.editor_config = dict([(k, str(v).lower() if isinstance(v, bool) else v) for (k, v) in conf['editor'].items()])

        super(WSGIApp, self).set_config(config_filename, conf, error)

    def on_app_exception(self, app_name):
        """Call when an exception occurs in a published application

        Return:
          - a WebOb response object
        """ 
        traceback.print_exc()

        return webob.exc.HTTPMovedPermanently(location='/'+self.name+'/exception/'+app_name)

    def set_publisher(self, publisher):
        """Register the publisher

        In:
          - ``publisher`` -- the publisher of the application
        """
        super(WSGIApp, self).set_publisher(publisher)

        self.publisher = publisher

    def start(self):
        """Call after each process start
        """
        super(WSGIApp, self).start()

        # For each published application, overwrite its ``on_exception()`` hook
        for (app, _, _) in self.publisher.get_registered_applications():
            if app is not self:
                app.on_exception = lambda request, response, name=app.name: self.on_app_exception(name)

        # Create the Comet push channel
        comet.channels.create(CHANNEL_ID, 'eval', history_size=self.max_nb_logs)

    def get_applications(self):
        """Return the published application objects

        Return:
          - list of the published applications
        """
        return [app for (app, _, _) in self.publisher.get_registered_applications() if (app is not self) and app.project_name and (app.project_name != 'nagare')]

    def create_root(self):
        """Create the application root component

        Return:
          - the root component
        """
        return super(WSGIApp, self).create_root('/'+self.name, self.get_applications, self.nagare_sources, self.editor_config)

# -----------------------------------------------------------------------------

app = WSGIApp(lambda *args: component.Component(workspace.WorkSpace(*args)))
