#--
# Copyright (c) 2008-2012 Net-ng.
# All rights reserved.
#
# This software is licensed under the BSD License, as described in
# the file LICENSE.txt, which you should have received as part of
# this distribution.
#--

"""Tree view of the source files and exceptions"""

from __future__ import with_statement

import os

import pkg_resources

from nagare import component, presentation, ajax

from nagare.ide import YUI_PREFIX

# -----------------------------------------------------------------------------

class Directory(object):
    """A filesystem directory"""

    def __init__(self, label, root, dirname, filenames, directories):
        """Initialization

        In:
          - ``label`` -- label to display
          - ``root`` -- the root tree
          - ``dirname`` -- path of this directory, relative to ``root``
          - ``filenames`` -- names of the files in this directory
          - ``directories`` -- the sub-directories in this directory as a list of tuples:
                                 - ``dirname``
                                 - ``filenames``
                                 - ``directories``
        """
        self.label = label
        self.root = root
        self.dirname = dirname
        self.filenames = filenames
        self.directories = directories

@presentation.render_for(Directory)
def render(self, h, *args):
    with h.li:
        h << self.label

        if self.directories or self.filenames:
            with h.ul:
                if self.directories:
                    # Recursive rendering of the sub-directories
                    h << [component.Component(Directory(os.path.basename(dir[0]), self.root, *dir)) for dir in self.directories]

                if self.filenames:
                    h << [h.li(filename, yuiConfig='{ "labelStyle": "ygtvlabel file", "uid" : "source@%s", "filename" : "%s" }' % ('/'.join((self.root, self.dirname, filename)), filename)) for filename in self.filenames]

    return h.root

# -----------------------------------------------------------------------------

class Directories(object):
    """A filesystem tree"""

    def __init__(self, roots, allow_extensions):
        """Initialization

        In:
          - ``roots`` -- list of filesystem roots, as tuples:
                         - label of the root
                         - path of the root
          - ``allow_extensions`` -- list of allowed file extensions
        """
        self.allow_extensions = tuple(allow_extensions)

        # Read and merge all the trees
        self.roots = [(label, root.replace('\\', '/'), self.load_directories(root)) for (label, root) in roots]

    def load_directories(self, root, dirname=''):
        """Read a filesystem tree

        In:
          - ``root`` -- path of the root

        Return:
          - recursive Python structure of the filesystem tree
        """
        files = []
        directories = []

        for filename in os.listdir(os.path.join(root, dirname)):
            pathname = os.path.join(root, dirname, filename)

            if os.path.isfile(pathname) and pathname.endswith(self.allow_extensions):
                files.append(filename)

            if os.path.isdir(pathname) and filename not in ('.svn', 'CVS'):
                directories.append(self.load_directories(root, os.path.join(dirname, filename)))

        return (dirname.replace('\\', '/'), files, directories)

@presentation.render_for(Directories)
def render(self, *args):
    return [component.Component(Directory(label, root, *directories)) for (label, root, directories) in self.roots]

# -----------------------------------------------------------------------------

class Tree(object):
    """Tree view of the currently published applications and their packages
    """
    def __init__(self, projects, allow_extensions, get_applications):
        """Initialization

        In:
          - ``projects`` -- the packages
          - ``allow_extensions`` -- list of allowed file extensions
          - ``get_applications` -- function to get the published applications
        """
        self.projects = []
        for project in sorted(projects):
            if isinstance(project, str):
                name = project
                project = project.replace('-', '_')
                parent = '..'
            else:
                name = project.project_name
                parent = ''

            # Use ``pkg_resources.resource_filename()`` to get the root of a packages sources
            self.projects.append(('Package ' + name, os.path.normpath(pkg_resources.resource_filename(project, parent))))

        self.allow_extensions = allow_extensions
        self.get_applications = get_applications

@presentation.render_for(Tree)
def render(self, h, comp, *args):
    h.head.css_url(YUI_PREFIX+'/treeview/assets/skins/sam/treeview.css')

    h.head.javascript_url(YUI_PREFIX+'/json/json-min.js')

    return comp.render(h, model='raw')

@presentation.render_for(Tree, model='raw')
def render(self, h, *args):
    if h.request.environ['wsgi.multiprocess']:
        apps = []
    else:
        apps = sorted([app.name for app in self.get_applications() if app.last_exception])

    with h.div:
        h << h.div(h.a('Reload', href='#', onclick='return nagare_getAndEval("reload")'), style='text-align: center', class_='tab_info')

        with h.div(id='treeview'):
            with h.ul:
                # Display the packages sources
                h << component.Component(Directories(self.projects, self.allow_extensions))

                # Display the exception labels
                for name in apps:
                    with h.li('Application ', name):
                        with h.ul:
                            h << h.li('Exception', yuiConfig='{ "labelStyle" : "ygtvlabel exception", "uid" : "exception@%s" }' % name)

        h << h.div(id='exceptions', syle='display: none ')
        h << h.script('''
            var treeview = setup_tree_view("treeview");
            exceptions_tabs(%s);    // Open the exceptions tabs
            ''' % ajax.py2js(apps, h))

    return h.root
