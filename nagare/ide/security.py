#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

import configobj
from peak.rules import when

from nagare import config
from nagare.security import common

class Authentication(common.Authentication):
    """Authentication manager for IP addresses

    This special authentication manager creates a pseudo-user with his id
    set to the IP address of the client
    """

    def get_ids(self, request, response):
        """Return the data associated with the connected user

        In:
          - ``request`` -- the web request object
          - ``response`` -- the web response object

        Return:
          - A tuple with the id of the user and a dictionary of its data
        """
        return (request.remote_addr, {})

    def check_password(self, username, password, **kw):
        """Authentication

        In:
          - ``username`` -- the user id
          - ``password`` -- the real password of the user
          - ``kw`` -- other data for the user

        Return:
          - True
        """
        return True

    def _create_user(self, username):
        """Create a basic user object

        In:
          - ``username`` -- the user id (here the IP address)

        Return:
          - the user object
        """
        return common.User(username)


class SecurityManager(Authentication, common.Rules):
    """Security manager for IP addresses

    This special security manager checks the IP address of the client
    against a set of allowed hosts
    """

    spec = { 'allow_hosts' : 'list(default=list())' }

    def __init__(self, allow_hosts=()):
        """Initialization
        """
        self.allow_hosts = allow_hosts

    def set_config(self, config_filename, conf, error):
        """Read the set of allowed hosts from the configuration file

        In:
          - ``config_filename`` -- the path to the configuration file
          - ``conf`` -- the ``ConfigObj`` object, created from the configuration file
          - ``error`` -- the function to call in case of configuration errors
        """
        conf = configobj.ConfigObj(conf, configspec=configobj.ConfigObj(self.spec))
        config.validate(config_filename, conf, error)

        self.allow_hosts = conf['allow_hosts']

    @when(common.Rules.has_permission, (object,))
    def _(self, user, perm, subject):
        """Only one security rule to check if the client is allowed"""
        return user.id in self.allow_hosts
