#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Sessions managed in memory

This session manager keeps:
  - the last recently used ``DEFAULT_NB_SESSIONS`` sessions
  - for each session, the last recently used ``DEFAULT_NB_STATES`` states
"""

import copy

from nagare.sessions.memory_sessions import SessionsBase

class SessionsWithMemoryStates(SessionsBase):
    """Sessions managers that keeps the objects graph in memory
    """
    def serialize(self, data):
        """Memorize an objects graph

        In:
          - ``data`` -- the objects graphs

        Return:
          - the tuple:
            - data to keep into the session
            - data to keep into the state
        """
        # Do nothing
        return (None, data)

    def deserialize(self, session_data, state_data):
        """Create the objects graph

        In:
          - ``session_data`` -- data from the session
          - ``state_data`` -- data from the state

        Out:
          - the objects graph
        """
        return copy.deepcopy(state_data) if self.states_history else state_data
