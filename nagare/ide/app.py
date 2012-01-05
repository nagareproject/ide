#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import configobj
import traceback
import cookielib

import webob
from nagare import component, wsgi, config, comet, security
from nagare.admin import util

from nagare.ide import CHANNEL_ID, workspace
import nagare.ide.log

class WSGIApp(wsgi.WSGIApp):
    """The Nagare IDE application
    """

    spec = {
            'editor' : {
                'theme' : 'string(default="white")',
                'tabshowspace' : 'boolean(default=True)',
                'autoindent' : 'boolean(default=True)',
                'closepairs' : 'boolean(default=False)',
                'highlightline' : 'boolean(default=False)',
                'fontsize' : 'string(default="10")',
                'tabsize' : 'string(default="4")'
            },

            'navigator' : {
                'nagare_sources' : 'boolean(default=False)',
                'allow_extensions' : 'list(default=list())'
            },

            'security' : {
                'manager' : 'string(default=nagare.ide.security:SecurityManager)'
            }
           }

    def __init__(self, root_factory):
        """Initialization
        """
        super(WSGIApp, self).__init__(root_factory)

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

        self.allow_extensions = conf['navigator']['allow_extensions']
        self.nagare_sources = conf['navigator']['nagare_sources']
        self.editor_config = dict([(k, str(v).lower() if isinstance(v, bool) else v) for (k, v) in conf['editor'].items()])

        # Create and configure the security manager
        # -----------------------------------------

        self.security = util.load_object(conf['security']['manager'])[0]()
        self.security.set_config(config_filename, conf['security'], error)

        super(WSGIApp, self).set_config(config_filename, conf, error)

    def on_app_exception(self, request, app_name):
        """Call when an exception occurs in a published application

        In:
          - ``request` -- the WebOb request object
          - ``app_name`` -- name (i.e URL) of the application where the exception occurs

        Return:
          - a WebOb response object
        """
        traceback.print_exc()

        location = '/'+self.name+'/exception/'+app_name

        if request.is_xhr or ('_a' in request.params):
            r = webob.exc.HTTPInternalServerError(headers={ 'X-Debug-URL' : location })
        else:
            r = webob.exc.HTTPTemporaryRedirect(location=location)

        return r

    def set_publisher(self, publisher):
        """Register the publisher

        In:
          - ``publisher`` -- the publisher of all the launched applications
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
                app.on_exception = lambda request, response, name=app.name: self.on_app_exception(request, name)

        # Create the Comet push channel
        comet.channels.create(CHANNEL_ID, 'eval', 10)

    def start_request(self, root, request, response):
        """A new request is received, setup its dedicated environment

        In:
          - ``root`` -- the application root component
          - ``request`` -- the web request object
          - ``response`` -- the web response object
        """
        super(WSGIApp, self).start_request(root, request, response)

        security.check_permissions('connection')

    def get_applications(self):
        """Return the published application objects

        Return:
          - list of the published applications
        """
        return [app for (app, _, _) in self.publisher.get_registered_applications() if (app is not self) and (app.project_name != 'nagare')]

    def create_root(self):
        """Create the application root component

        Return:
          - the root component
        """
        return super(WSGIApp, self).create_root('/'+self.name, self.allow_extensions, self.get_applications, self.nagare_sources, self.editor_config)

    def __call__(self, environ, start_response):
        """WSGI interface

        In:
          - ``environ`` -- dictionary of the received elements
          - ``start_response`` -- callback to send the headers to the browser

        Return:
          - the content to send back to the browser
        """
        # Clean-up the cookies because Bespin can generate invalid cookies for WebOb
        cookies = environ.get('HTTP_COOKIE')
        if cookies:
            cookies = cookielib.split_header_words([cookies])
            cookies = [(k, v) for (k, v) in cookies[0] if not k.startswith('viewData_Nagare_')]
            environ['HTTP_COOKIE'] = cookielib.join_header_words([cookies])

        return super(WSGIApp, self).__call__(environ, start_response)

# -----------------------------------------------------------------------------

app = WSGIApp(lambda *args: component.Component(workspace.WorkSpace(*args)))
