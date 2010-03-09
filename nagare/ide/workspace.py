#--
# Copyright (c) 2008, 2009, 2010 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Nagare IDE interface"""

from __future__ import with_statement

import os

import webob

from nagare import presentation, component, serializer, ajax, comet
from nagare.namespaces import xhtml

from nagare.ide import YUI_PREFIX, CHANNEL_ID
from nagare.ide import bespin_editor, tree, error

# -----------------------------------------------------------------------------

import pkg_resources

class WorkSpace(object):
    def __init__(self, url, get_applications, nagare_sources, editor_config):
        """Initialization

        In:
          - ``
          - ``get_applications` -- function to get the published applications
          - ``nagare_sources`` -- Are the Nagare core sources included ?
          - ``editor_config`` -- the Bespin editor configuration as a dict
        """
        self.url = url
        self.get_applications = get_applications
        self.editor_config = editor_config

        projects = set([app.project_name for app in get_applications()])

        if nagare_sources:
            projects.add(pkg_resources.Requirement.parse('nagare'))

        self.directories_view = component.Component(tree.Tree(projects, get_applications))

    def get_exception(self, app_name):
        """Return the last exception of an application

        In:
          - ``app_name`` -- name of the application

        Return:
          - a tuple (request, exception)
        """
        exceptions = [app.last_exception for app in self.get_applications() if (app.name == app_name) and app.last_exception]
        if not exceptions:
            return (None, None)

        return exceptions[0]

@presentation.render_for(WorkSpace)
def render(self, h, comp, *args):
    h.head.css_url(YUI_PREFIX+'/reset-fonts-grids/reset-fonts-grids.css')
    h.head.css_url(YUI_PREFIX+'/assets/skins/sam/resize.css')
    h.head.css_url(YUI_PREFIX+'/assets/skins/sam/layout.css')
    h.head.css_url(YUI_PREFIX+'/container/assets/skins/sam/container.css')
    h.head.css_url(YUI_PREFIX+'/button/assets/skins/sam/button.css')

    h.head.javascript_url(YUI_PREFIX+'/yahoo-dom-event/yahoo-dom-event.js')
    h.head.javascript_url(YUI_PREFIX+'/dragdrop/dragdrop-min.js')
    h.head.javascript_url(YUI_PREFIX+'/element/element-min.js')

    h.head.javascript_url(YUI_PREFIX+'/resize/resize-min.js')
    h.head.javascript_url(YUI_PREFIX+'/layout/layout-min.js')

    h.head.javascript_url(YUI_PREFIX+'/tabview/tabview-min.js')

    h.head.javascript_url(YUI_PREFIX+'/button/button-min.js')
    h.head.javascript_url(YUI_PREFIX+'/container/container-min.js')

    h.head.javascript_url('ide.js')

    h.head << h.head.title('Nagare IDE')

    # Dummy asynchronous element to force the inclusion of the Nagare Ajax manager
    xhtml.AsyncRenderer(h).a.action(lambda: None)

    with h.body(class_='yui-skin-sam'):
        # The central panel with the tabs and the Bespin editor
        with h.div(id='content'):
            h << h.div(id='tabview', class_='yui_navset')
            h << component.Component(bespin_editor.Editor(self.editor_config))

        h << h.script('var tabview = setupTabView("tabview")')

        # The left panel with the applications and packages tree
        h << h.div(self.directories_view, id='tree', style='padding: 2px')

        # The bottom panel with the logs
        with h.table(id='logs'):
            with h.thead:
                h << h.tr(h.th('Time'), h.th('Source'), h.th('Level'), h.th('Description', width='100%'))

            h << h.tbody

        with h.script:
            h << '''
                var layout = new YAHOO.widget.Layout({
                    units: [
                        { position: 'left', body: 'tree', width: '300px', header: 'Applications', collapse: true, resize: true, scroll: true, gutter: '0 5 0 0' },
                        { position: 'center', body: 'content', scroll: true },
                        { position: 'bottom', body: 'logs', height: '300px', header: 'Logs', collapse: true, resize: true, scroll: true, gutter: '5 0 0 0' }
                    ]}).render();

                // Function to resize the Bespin editor when the central panel is resized
                layout.getUnitByPosition('center').addListener('resize', function(e, p) {
                    var tab = tabview.get('activeTab');
                    if(tab) { tab.onResize(p) }
                }, layout.getUnitByPosition('center'), true);
                '''

        # The Comet push channel
        h << component.Component(comet.channels[CHANNEL_ID])

    h.head.css_url('ide.css')

    return h.root

# -----------------------------------------------------------------------------

@presentation.render_for(WorkSpace, model='reload')
def render(self, h, comp, *args):
    """A full javascript view to update the left panel content"""
    update = ajax.Update(lambda h: self.directories_view.render(h, model='raw'), component_to_update='tree')
    return update._generate_render(h)(h)

@presentation.render_for(WorkSpace, model='exception')
def render(self, h, comp, *args):
    """The view where an application is redirected when an error occurs"""

    # Get the javascript 'reload' view
    view = comp.render(xhtml.AsyncRenderer(), model='reload')
    js = serializer.serialize(view, h.request, h.response, False) #.encode('utf-8')

    # Push it to the IDE
    comet.channels.send(CHANNEL_ID, js)

    h.response.content_type = 'text/html'

    request = self.get_exception(self.app_in_error)[0]

    h.head.css_url('/static/nagare/application.css')
    h.head.css_url('ide.css')

    h.head << h.head.title('Exception in application ' + self.app_in_error)

    with h.div(class_='mybody'):
        with h.div(id='myheader'):
            h << h.a(h.img(src='/static/nagare/img/logo.gif'), id='logo', href='http://www.nagare.org/', title='Nagare home')
            h << h.span('Exception', id='title')

        with h.div(id='main'):
            with h.div(class_='warning'):
                h << h.span('An exception occured in the application ', h.i('/'+self.app_in_error))

                with h.div:
                    h << 'You can:'

                    with h.ul:
                        h << h.li(h.a('Switch to the Nagare IDE window', href='#', target='nagare_ide_window'))
                        h << h.li(h.a('Open a new IDE window', href=self.url, target='nagare_ide_window'))
                        if request:
                            h << h.li(h.a('Retry the last action', href=request.url))
                        h << h.li(h.a('Open a new session in application /'+self.app_in_error, href='/'+self.app_in_error))

            h << h.div(u'\N{Copyright Sign} ', h.a('Net-ng', href='http://www.net-ng.com'), u'\N{no-break space}', align='right')

    h << h.div(' ', class_='footer')

    return h.root

@presentation.render_for(WorkSpace, model='app_exception')
def render(self, h, comp, *args):
    """The view of an application exception"""

    (request, exception) = self.get_exception(self.app_in_error)
    if not request:
        return ''

    traceback = component.Component(error.IDEException(request, *exception))

    # This is a javascript asynchronous view
    update = ajax.Update(traceback.render, component_to_update='exception')
    return update._generate_render(h)(h)

# -----------------------------------------------------------------------------

# URLs mapping
# ------------

@presentation.init_for(WorkSpace, "url == ('reload',)")
def init(self, url, comp, *args):
    comp.becomes(self, model='reload')

@presentation.init_for(WorkSpace, "(len(url) == 2) and (url[0] == 'exception')")
def init(self, url, comp, *args):
    self.app_in_error = url[1]
    comp.becomes(self, model='exception')

@presentation.init_for(WorkSpace, "(len(url) == 2) and (url[0] == 'exception_tab')")
def init(self, url, comp, *args):
    self.app_in_error = url[1]
    comp.becomes(self, model='app_exception')

# -----------------------------------------------------------------------------

# Bepin URLs
# ----------

@presentation.init_for(WorkSpace, "(http_method == 'GET') and (url[0] == 'register') and (url[1] == 'userinfo')")
def init(self, url, comp, http_method, request):
    exc = webob.exc.HTTPOk()
    exc.body = '{}'
    raise exc

@presentation.init_for(WorkSpace, "(http_method == 'PUT') and (url[0] == 'file') and (url[1] == 'at')")
def init(self, url, comp, http_method, request):
    """Writing a file"""
    filename = os.path.join(*url[3:])

    with open(os.path.sep+filename, 'w') as f:
        f.write(request.body)

    raise webob.exc.HTTPOk()

@presentation.init_for(WorkSpace, "(http_method == 'GET') and (url[0] == 'file') and (url[1] == 'at')")
def init(self, url, comp, http_method, request):
    """Reading a file"""
    url = url[2:]

    exc = webob.exc.HTTPOk()
    exc.empty_body = True

    if url[0] == 'BespinSettings':
        raise exc

    filename = os.path.sep+os.path.join(*url[1:])

    if os.path.isfile(filename):
        with open(os.path.sep+filename, 'r') as f:
            exc.body = f.read()

    raise exc
