# Encoding: utf-8

#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Frames and exceptions components"""

from __future__ import with_statement

import sys
import os
import linecache
from StringIO import StringIO
from pprint import pformat
import threading
import compiler
import traceback

from pygments import highlight as pygments_highlight
from pygments.lexers import PythonConsoleLexer, PythonLexer, PythonTracebackLexer
from pygments.formatters import HtmlFormatter

from webob import Request

from nagare import component, presentation, var

NBSP = u'\N{NO-BREAK SPACE}'

# ----------------------------------------------------------

def python_highlight(code, renderer, wrapper, hl_line=-1, python_console=False, **kw):
    """Syntax highlighting of Python code

    In:
      - ``code`` -- the Python code
      - ``renderer`` -- a HTML renderer
      - ``wrapper`` -- the wrapper HTML element
      - ``hl_line`` -- line to highlight
      - ``python_console`` -- is ``code`` a Python console capture or Python source ?

    Return:
      - a DOM tree
    """
    lexer = PythonConsoleLexer() if python_console else PythonLexer()
    source = pygments_highlight(code, lexer, HtmlFormatter(**kw))

    lines = []
    for (n, line) in enumerate(source.splitlines()):
        i = line.find('<')
        if i != -1:
            # Replace the starting spaces by NBSP characters
            line = NBSP*i + line[i:]

        if n == hl_line:
            line = '<span class="source-highlight">%s</span>' % line

        lines.append(line)

    html = renderer.parse_htmlstring('<br>'.join(lines))
    return wrapper(html[0][0][0][:], class_='source highlight')

# -----------------------------------------------------------------------------

class IDEFrameContext(object):
    """Context (local and globals vars) of a Python frame"""

    exec_lock = threading.Lock()

    def __init__(self, locals, globals):
        """Initialization

        In:
          - ``locals`` -- local vars dict
          - ``globals`` -- global vars dict
        """
        self.locals = locals
        self.globals = globals

        self.executions = ''  # Concatenation of all the ``self.execute(code)`` calls
        self.expanded_locals = {}

        self.short_input = var.Var(True)

    def execute(self, code):
        """Execute a Python code in this context

        In:
          - ``code`` -- the Python code
        """
        # Build an AST tree from the Python code, to get the line number of each statement
        try:
            nodes = compiler.parse(code).getChildNodes()[0].getChildNodes()
            lines = [node.lineno-1 for node in nodes]
        except:
            self.executions += '>>> ' + code + '\n' + ''.join(traceback.format_exception(*sys.exc_info())[4:])
            return

        code = code.splitlines()

        with IDEFrameContext.exec_lock:
            stdout = sys.stdout

            try:
                # Iterate over all the statements
                for (a, b) in zip(lines, lines[1:]+[None]):
                    sys.stdout = StringIO()

                    source = code[a:b]

                    try:
                        # Execute the statement using this local and global context
                        exec compile('\n'.join(source), '<web>', 'single', 0, 1) in self.locals, self.globals
                    except:
                        print ''.join(traceback.format_exception(*sys.exc_info())[2:]).rstrip()

                    self.executions += '\n'.join([('... ' if line.startswith(' ') else '>>> ') + line for line in source]) + '\n' + sys.stdout.getvalue()
            finally:
                sys.stdout = stdout


@presentation.render_for(IDEFrameContext)
def render(self, h, *args):
    pyexpr = var.Var('')

    with h.div:
        if self.executions:
            with h.div(style='background-color: #f3f2f1'):
                h << python_highlight(self.executions, h, h.pre(style='background-color: #f3f2f1; white-space: pre-wrap'), python_console=True)

        with h.form(onsubmit="return false"):
            h << (h.input if self.short_input() else h.textarea(rows=4))(style='width: 100%').action(pyexpr)
            h << h.br
            h << h.input(type='submit', value='Execute').action(lambda: self.execute(pyexpr()))

            if self.short_input():
                h <<  ' '
                h << h.input(type='submit', value='Expand').action(lambda: self.short_input(False))

        local_vars = self.locals
        if not local_vars:
            h << h.i('No local vars')
        else:
            with h.table:
                for (i, (name, value)) in enumerate(sorted(local_vars.items())):
                    value = pformat(value)
                    value, expand = value[:100], value[100:]

                    with h.tr(class_='odd' if i % 2 else 'even'):
                        h << h.td(h.b(name), valign='top')
                        with h.td(style='overflow: auto; padding: 0 4px 0 10px'):
                            if expand and not self.expanded_locals.get(name):
                                expand = h.a('...', style='background-color: #dadada').action(lambda name=name: self.expanded_locals.setdefault(name, True))

                            h << h.code(value, expand)

    return h.root

# -----------------------------------------------------------------------------

class IDEFrame(object):
    """A Python frame
    """
    def __init__(self, tb):
        """Initialization

        In:
          - ``frame`` -- ``tb.tb_frame`` is the Python frame
        """
        frame = tb.tb_frame

        self.lineno = tb.tb_lineno
        self.filename = frame.f_code.co_filename
        self.name = frame.f_code.co_name
        self.modname = frame.f_globals.get('__name__')

        self.expanded = False
        self.context = component.Component(IDEFrameContext(frame.f_locals, frame.f_globals))

    def get_source_lines(self, context=0):
        """Fetch the Python lines of code of this frame

        In:
          - ``context`` -- number of lines to fetch before and after the frame line
        """
        if not self.filename or not self.lineno:
            return ''

        return ''.join([' '+linecache.getline(self.filename, lineno) for lineno in range(self.lineno-context, self.lineno+context+1)])

@presentation.render_for(IDEFrame)
def render(self, h, comp, *args):
    with h.li:
        if self.expanded:
            h << { 'class' : 'expanded' }

        with h.div(title=self.filename or '?'):
            h << h.span('Module ', style='color: #555')
            h << (self.modname or '?') << ':' << (self.lineno or '?')
            h << h.span(' in ', style='color: #555') << (self.name or '?')

        with h.ul:
            source = self.get_source_lines(0)

            if source:
                with h.li:
                    if self.expanded:
                        h << { 'class' : 'expanded' }

                    with h.span:
                        js = '''if(YAHOO.env.ua.ie) { YAHOO.util.Event.stopEvent(window.event); }
                                open_tab({
                                    uid: "source@%(pathname)s",
                                    pathname: "%(pathname)s",
                                    filename: "%(filename)s",
                                    lineno: %(lineno)d
                          })''' % { 'pathname' : self.filename.replace('\\', '/'), 'filename' : os.path.basename(self.filename), 'lineno' : self.lineno }
                        h << h.a('edit', href='#', onclick=js) << NBSP
                        h << python_highlight(source, h, h.span)

                    with h.ul:
                        with h.li(yuiConfig='{ "not_expandable" : true }'):
                            source = self.get_source_lines(2)
                            h << python_highlight(source, h, h.pre(style='background-color: #f3f2f1'), hl_line=2, linenos='inline', linenostart=max(0, self.lineno-2))

            with h.li('Context', style='color: #555'):
                with h.ul:
                    with h.li(yuiConfig='{ "not_expandable" : true }'):
                        h << h.div(self.context.render(h.AsyncRenderer()))

    return h.root

@presentation.render_for(IDEFrame, model='short')
def render(self, h, *args):
    h.head.css('pygments', HtmlFormatter(nobackground=True).get_style_defs('.highlight'))

    with h.div(title=self.filename or '?'):
        h << h.span('Module ', style='color: #aaa') << (self.modname or '?') << h.span(' in ', style='color: #aaa') << (self.name or '?')

        source = self.get_source_lines(2)
        h << python_highlight(source, h, h.pre, hl_line=2, linenos='inline', linenostart=max(0, self.lineno-2))

    return h.root

# -----------------------------------------------------------------------------

class IDEException(object):
    """A Python exception
    """
    def __init__(self, request, exc_type, exc_value, tb):
        """Initialization

        In:
          - ``request`` -- the WebOb request where the exception occured
          - ``exc_type`` -- the exception type
          - ``exc_value`` -- the exception value
          - ``tb`` -- the traceback
        """
        self.request = request
        self.exception_name = exc_type.__name__
        self.exception_value = str(exc_value)

        self.tb = ''.join(traceback.format_exception(exc_type, exc_value, tb))

        # From the traceback, create a list of frame components
        # -----------------------------------------------------

        self.frames = []
        while tb:
            frame = IDEFrame(tb)
            self.frames.append(component.Component(frame))
            tb = tb.tb_next

        frame.expanded = True;  # The last frame will be displayed expanded

@presentation.render_for(IDEException)
def render(self, h, comp, *args):
    with h.div:
        # Exception informations
        with h.div(class_='tab_info'):
            h << h.span(u'⇝', style='color: #f00') << NBSP
            h << self.exception_name << ': ' << self.exception_value

        with h.div(style='padding: 10px', id='frames'):
            with h.ul:
                # Request informations (CGI and WSGI variables)
                h << component.Component(self.request, model='ide')

                # Textual traceback
                with h.li('Text Traceback'):
                    lexer = PythonTracebackLexer()
                    source = pygments_highlight(self.tb, lexer, HtmlFormatter())
                    h << h.ul(h.li(h.parse_htmlstring(source), yuiConfig='{ "not_expandable" : true }'))

                # Interactive traceback
                with h.li('Interactive Traceback', class_='expanded'):
                    h << h.ul(self.frames)

        h << h.script('''
        var frames = new YAHOO.widget.TreeView("frames");

        frames.subscribe("clickEvent", function(e) { return !e.node.data.not_expandable; });
        frames.render();

        // Don't let the TreeView widget catch the keydown events for our <input> or <textarea> fields
        var fn = YAHOO.util.Event.getListeners(frames.getEl(), "keydown")[0].fn;
        YAHOO.util.Event.removeListener(frames.getEl(), "keydown");
        YAHOO.util.Event.addListener(frames.getEl(), "keydown", function(e) {
            if(e.target) {
                if(e.target.tagName != "INPUT" && e.target.tagName != "TEXTAREA") { fn.call(frames, e); }
                return false;
            }
        });

        ''')

    return h.root

@presentation.render_for(IDEException, model='tree_item')
def render(self, h, *args):
    return h.li('Exception', yuiConfig='{ "labelStyle": "ygtvlabel exception" }')

# -----------------------------------------------------------------------------

# WSGI vars not to display
wsgi_hide_vars = (
                    'paste.config', 'wsgi.errors', 'wsgi.input',
                    'wsgi.multithread', 'wsgi.multiprocess',
                    'wsgi.run_once', 'wsgi.url_scheme'
                   )

# Concurrent env. type
process_combos = {
                    # (multiprocess, multithread, run_once)
                    (0, 0, 0): 'Non-concurrent server',
                    (0, 1, 0): 'Multithreaded',
                    (1, 0, 0): 'Multiprocess',
                    (1, 1, 0): 'Multi process AND threads (?)',
                    (0, 0, 1): 'Non-concurrent CGI',
                    (0, 1, 1): 'Multithread CGI (?)',
                    (1, 0, 1): 'CGI',
                    (1, 1, 1): 'Multi thread/process CGI (?)',
                   }

# HTML view of a WebOb request, for the IDE
# -----------------------------------------

@presentation.render_for(Request, model='ide')
def render(self, h, *args):
    with h.li:
        h << h.div('URL: ', h.a(self.url, href='#', onclick='window.open("%s", "nagare_app_window")' % self.url))

    with h.li('CGI Variables'):
        with h.ul:
            with h.li(yuiConfig='{ "not_expandable" : true }'):
                with h.table(class_='alternate_rows'):
                    for (name, value) in sorted(self.environ.items()):
                        if name.isupper() and value:
                            with h.tr:
                                h << h.td(h.b(name), valign='top')
                                h << h.td(repr(value), style='overflow: auto; padding: 0 4px 0 10px')


    with h.li('WSGI Variables'):
        with h.ul:
            with h.li(yuiConfig='{ "not_expandable" : true }'):
                with h.table(class_='alternate_rows'):
                    environ = self.environ.copy()

                    version = environ.pop('wsgi.version')
                    if  version != (1, 0):
                        environ['wsgi.version'] = '%d.%d' % version

                    process_combo = map(environ.get, ('wsgi.multiprocess', 'wsgi.multithread', 'wsgi.run_once'))
                    environ['wsgi.process'] = process_combos[tuple(process_combo)]

                    for (name, value) in sorted(environ.items()):
                        if not name.isupper() and (name not in wsgi_hide_vars):
                            with h.tr:
                                h << h.td(h.b(name), valign='top')
                                h << h.td(repr(value), style='overflow: auto; padding: 0 4px 0 10px')

    return h.root
