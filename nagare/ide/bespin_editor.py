#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Create a Bespin editor widget into a ``<div>``"""

from __future__ import with_statement

from nagare import presentation

class Editor:
    def __init__(self, settings):
        """Initialization

        In:
          - ``settings`` -- the Bespin editor configuration dict
        """
        self.settings = settings
        self.settings['reload'] = 'true'
        self.settings['dontstealfocus'] = 'true'

@presentation.render_for(Editor)
def render(self, h, *args):
    h.head.javascript_url('js/dojo/dojo.js')
    h.head.javascript_url('js/bespin/editor/embed.js')

    h.head.javascript_url('js/bespin/client/server.js')
    h.head.javascript_url('js/bespin/client/session.js')
    h.head.javascript_url('js/bespin/client/filesystem.js')
    h.head.javascript_url('js/bespin/page/editor/init.js')

    settings = ['settings.set("%s", "%s");' % t for t in self.settings.items()]

    h << h.div(id='editor', style='width: 1px; height: 1px') # The editor container

    with h.script:
        # Bind '^S' to the save action
        h << '''bespin.subscribe("authenticated", function() {
            bespin.get("editor").editorKeyListener.bindKeyString("CMD", bespin.util.keys.Key.S, function() {  tabview.get('activeTab').save() }, "Save");

            var settings = bespin.get('settings');
            %s
        });''' % '\n'.join(settings)

        h << '''bespin.subscribe("editor:openfile:opensuccess", on_file_opened);'''

    return h.root
