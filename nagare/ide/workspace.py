#--
# Copyright (c) 2008-2012 Net-ng.
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

from pygments import highlight
from pygments.lexers import guess_lexer_for_filename
from pygments.formatters import HtmlFormatter

from nagare import presentation, component, serializer, ajax, comet

from nagare.ide import YUI_PREFIX, CHANNEL_ID
from nagare.ide import bespin_editor, tree, error

# -----------------------------------------------------------------------------

import pkg_resources

class WorkSpace(object):
    def __init__(self, url, allow_extensions, get_applications, nagare_sources, editor_config):
        """Initialization

        In:
          - ``url`` -- url of this IDE application
          - ``allow_extensions`` -- list of allowed file extensions
          - ``get_applications` -- function to get the published applications
          - ``nagare_sources`` -- Are the Nagare core sources included ?
          - ``editor_config`` -- the Bespin editor configuration as a dict
        """
        self.url = url
        self.get_applications = get_applications
        self.editor_config = editor_config

        projects = set([app.project_name for app in get_applications() if app.project_name])

        if nagare_sources:
            projects.add(pkg_resources.Requirement.parse('nagare'))

        self.directories_view = component.Component(tree.Tree(projects, allow_extensions, get_applications))

    def get_exception(self, app_name):
        """Return the last exception of an application

        In:
          - ``app_name`` -- name of the application

        Return:
          - a tuple (request, exception)
        """
        exceptions = [app.last_exception for app in self.get_applications() if (app.name == app_name) and app.last_exception]
        if not exceptions:
            return (None, (None, None, None))

        return exceptions[0]

@presentation.render_for(WorkSpace)
def render(self, h, comp, *args):
    h.head.css_url(YUI_PREFIX+'/reset-fonts-grids/reset-fonts-grids.css')
    h.head.css_url(YUI_PREFIX+'/assets/skins/sam/resize.css')
    h.head.css_url(YUI_PREFIX+'/assets/skins/sam/layout.css')
    h.head.css_url(YUI_PREFIX+'/container/assets/skins/sam/container.css')
    h.head.css_url(YUI_PREFIX+'/button/assets/skins/sam/button.css')

    h.head.css('pygments', HtmlFormatter(nobackground=True).get_style_defs('.highlight'))
    h.head.css('pygments_linenos', '.linenos pre { color: #aaa; margin-right: 10px }')

    h.head.javascript_url(YUI_PREFIX+'/yahoo-dom-event/yahoo-dom-event.js')
    h.head.javascript_url(YUI_PREFIX+'/dragdrop/dragdrop-min.js')
    h.head.javascript_url(YUI_PREFIX+'/element/element-min.js')

    h.head.javascript_url(YUI_PREFIX+'/resize/resize-min.js')
    h.head.javascript_url(YUI_PREFIX+'/layout/layout-min.js')

    h.head.javascript_url(YUI_PREFIX+'/tabview/tabview-min.js')
    h.head.javascript_url(YUI_PREFIX+'/treeview/treeview-min.js')

    h.head.javascript_url(YUI_PREFIX+'/button/button-min.js')
    h.head.javascript_url(YUI_PREFIX+'/container/container-min.js')

    h.head.javascript_url('ide.js')

    h.head << h.head.title('Nagare IDE')

    # Dummy asynchronous element to force the inclusion of the Nagare Ajax manager
    h.AsyncRenderer().a.action(lambda: None)

    multiprocess = h.request.environ['wsgi.multiprocess']

    with h.body(class_='yui-skin-sam'):
        # The central panel with the tabs and the Bespin editor
        with h.div(id='content'):
            h << h.div(id='tabview', class_='yui_navset')
            h << component.Component(bespin_editor.Editor(self.editor_config))

        h << h.script('var tabview = setup_tab_view("tabview")')

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
                 '''

            if not multiprocess:
                 h << '''
                        { position: 'bottom', body: 'logs', height: '300px', header: 'Logs', collapse: true, resize: true, scroll: true, gutter: '5 0 0 0' }
                      '''

            h << '''
                    ]}).render();

                 // Function to resize the Bespin editor when the central panel is resized
                 layout.getUnitByPosition('center').addListener('resize', function(e, p) {
                     var tab = tabview.get('activeTab');
                     if(tab) { tab.onResize(p) }
                 }, layout.getUnitByPosition('center'), true);
                 '''

        if not multiprocess:
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
    (request, (exc_type, exc_value, tb)) = self.get_exception(self.app_in_error)

    if request is None:
        raise webob.exc.HTTPTemporaryRedirect(location='/'+self.app_in_error)

    # Get the javascript 'reload' view
    view = comp.render(h.AsyncRenderer(request=h.request, response=h.response, async_header=True), model='reload')
    js = serializer.serialize(view, '', '', False)[1] #.encode('utf-8')

    # Push it to the IDE
    comet.channels.send(CHANNEL_ID, js+';')

    h.response.content_type = 'text/html'

    h.head.css('exception', '''
        .exception { margin: 40px 40px 40px 0; background-color: #f3f2f1 }
        .source { font-size: 70%; padding-left: 20px }
        #content { margin-left: 0 }
        body { font-size: 17px }
    ''')

    h.head.css_url('/static/nagare/application.css')
    h.head.css_url('ide.css')

    h.head << h.head.title('Exception in application ' + self.app_in_error)

    with h.div(id='body'):
        h << h.a(h.img(src='/static/nagare/img/logo_small.png'), id='logo', href='http://www.nagare.org/', title='Nagare home')

        with h.div(id='content'):
            h << h.div('Exception', id='title')

            with h.div(id='main'):
                with h.div(class_='warning'):
                    h << h.span('An exception occured in the application ', h.i('/'+self.app_in_error))

                with h.div(class_='exception'):
                    h << h.b(exc_type.__name__, ': ', str(exc_value))

                    while tb.tb_next:
                        tb = tb.tb_next

                    h << component.Component(error.IDEFrame(tb), model='short')

                with h.div:
                    h << 'You can:'

                    with h.ul:
                        h << h.li(h.a('Switch to the Nagare IDE window', href='#', target='nagare_ide_window'))
                        h << h.li(h.a('Open a new IDE window', href=self.url, target='nagare_ide_window'))
                        if request:
                            h << h.li(h.a('Retry the last action', href=request.url))
                        h << h.li(h.a('Open a new session in application /'+self.app_in_error, href='/'+self.app_in_error))

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

# Bespin URLs
# -----------

@presentation.init_for(WorkSpace, "(http_method == 'GET') and (url[0] == 'register') and (url[1] == 'userinfo')")
def init(self, url, comp, http_method, request):
    response = webob.exc.HTTPOk()
    response.body = '{}'
    raise response

@presentation.init_for(WorkSpace, "(http_method == 'PUT') and (url[0] == 'file') and (url[1] == 'at')")
def init(self, url, comp, http_method, request):
    """Writing a file"""
    filename = os.path.sep.join(url[3:])
    if not os.path.isabs(filename):
        filename = os.path.sep + filename

    with open(filename, 'w') as f:
        f.write(request.body)

    raise webob.exc.HTTPOk()

@presentation.init_for(WorkSpace, "(http_method == 'GET') and (url[0] == 'file') and (url[1] == 'at') and (url[2] == 'Nagare')")
def init(self, url, comp, http_method, request):
    """Reading a file"""
    url = url[2:]

    response = webob.exc.HTTPOk()
    response.empty_body = True

    if url[0] == 'BespinSettings':
        raise response

    filename = os.path.sep.join(url[1:])
    if not os.path.isabs(filename):
        filename = os.path.sep + filename

    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            response.body = f.read()

    raise response

@presentation.init_for(WorkSpace, "(http_method == 'GET') and (url[0] == 'source') and (url[1] == 'at') and (url[2] == 'Nagare')")
def init(self, url, comp, http_method, request):
    """Generating a syntax highlighted view of a file"""
    filename = os.path.sep.join(url[3:])
    if not os.path.isabs(filename):
        filename = os.path.sep + filename

    lexer = guess_lexer_for_filename(filename, '')
    formatter = HtmlFormatter(linenos='table')

    with open(filename) as f:
        source = highlight(f.read(), lexer, formatter)

    response = webob.exc.HTTPOk()

    response.content_type = 'text/plain'
    response.unicode_body = u'nagare_updateNode("%s", %s);' % (request.params['id'], ajax.py2js(source, None))

    raise response
