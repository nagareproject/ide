//--
// Copyright (c) 2008-2012 Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

YAHOO.namespace('nagare');

// Base class of the tab objects
// -----------------------------

YAHOO.nagare.BaseTab = function(info) {
    // Initialization
    //
    // In:
    //   - ``info.label`` -- label of the tab
    //   - ``info.uid`` -- UID of the tab
    info.label = info.label + ' <span title="close" class="tab_close"></span>';
    YAHOO.nagare.BaseTab.superclass.constructor.call(this, info);

    // ``this.close()`` is called when clicking on the 'close' icon of a tab
    YAHOO.util.Event.on(this.getElementsByClassName('tab_close')[0], 'click', function(e, t) {
        t.close(tabview);
    }, this);

    this.uid = info.uid;    // Each tab has a unique ID
}

YAHOO.extend(YAHOO.nagare.BaseTab, YAHOO.widget.Tab, {
    onEnter: function(treeview, editor_id, editor) {
        // Focus on this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object

        // Put the focus on the associated entry in the treeview
        var node = treeview.getNodeByProperty('uid', this.uid);
        if(node && node.getEl()) {
            //node.focus();
        }
    },

    onExit: function(treeview, editor_id, editor) {
        // Focus out of this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object
    },

    onResize: function(content) {
        // Method called when the gobal layout is resized
        //
        // In:
        //   - ``content`` -- the YUI central panel object where the tabview is rendered
    },

    close: function(tabview) {
        // Delete this tab
        //
        // In:
        //   - ``tabview`` -- the YUI treeview object
        tabview.removeTab(this);
    }
});


// Tab displaying an iteractive Python exception
// ---------------------------------------------

YAHOO.nagare.ExceptionTab = function(info) {
    // Initialization
    //
    // In:
    //   - ``info.label`` -- label of the tab
    //   - ``info.uid`` -- UID of the tab
    //   - ``info.app`` -- name of the application where the exception occured

    // Create a new ``<div>`` element with id ``exception`` to receive the
    // content to display

    // Delete the current ``id="exception"`` attribute
    var div = document.getElementById('exception')
    if(div) {
        div.removeAttribute('id');
    }

    // Create the new ``<div>``
    div = document.createElement('div');
    div.setAttribute('id', 'exception');
    document.getElementById('exceptions').appendChild(div);

    // Ajax request to retrieve the exception content
    nagare_getAndEval('exception_tab/'+info.app);

    info.label = 'Exception in <i>' + info.app + '</i>'
    info.contentEl = div;

    // Create the tab
    YAHOO.nagare.ExceptionTab.superclass.constructor.call(this, info);
}

YAHOO.extend(YAHOO.nagare.ExceptionTab, YAHOO.nagare.BaseTab, {
    onEnter: function(treeview, editor_id, editor) {
        // Focus on this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object

        // Put the focus on the associated entry in the treeview
        YAHOO.nagare.ExceptionTab.superclass.onEnter.call(this, treeview, editor_id, editor);

        // Display the ``<div>`` where the exception content was loaded
        YAHOO.util.Dom.setStyle(this.get('contentEl'), 'display', 'block');
    },

    onExit: function(treeview, editor_id, editor) {
        // Focus out of this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object

        // Hide the ``<div>`` where the exception content was loaded
        YAHOO.util.Dom.setStyle(this.get('contentEl'), 'display', 'none');
    }
});


// Tab displaying a editable Python source code
// --------------------------------------------

function create_action_event() {
    // Create an event for the Bespin actions manager
    //
    // Return:
    //   - an event with a ``pos`` attribute containing the Bespin cursor context
    return { pos: bespin.editor.utils.copyPos(bespin.get('editor').cursorManager.getCursorPosition()) };
}

function get_actions_manager() {
    // Return the Bespin actions manager
    //
    // Return:
    //   - the actions manager
    return bespin.get('editor').ui.actions;
}

function confirm(action) {
    // Helper action displaying a yes/no dialog
    //
    // In:
    //   - ``action`` -- callback to call when the 'Yes' choice is selected
    var confirm = new YAHOO.widget.SimpleDialog('_no_div_', {
        width: '20em',
        fixedcenter: true,
        modal: true,
        text: 'Do you really want to discard the changes ?',
        icon: YAHOO.widget.SimpleDialog.ICON_WARN,
        close: false,
        buttons: [
            { text: 'Yes', handler: function() { this.hide(); action(); } },
            { text: 'No',  handler: function() { this.hide(); } }
        ]
    });

    confirm.setHeader('File not save');
    confirm.render(document.body);
}

YAHOO.nagare.EditableSourceTab = function(info) {
    // Initialization
    //
    // In:
    //   - ``info.pathname`` -- complete pathname of the source file on the server
    //   - ``info.filename`` -- filename part of the pathname
    info.label = '<span title="' + info.pathname + '">' + info.filename + '</span>'

    // The icon bar
    info.content =  '<div class="tab_info">\
                       <img src="/static/ide/images/icn_save.png" title="Save">\
                       <img src="/static/ide/images/icn_reload.png" title="Reload">\
                       &nbsp;\
                       <img src="/static/ide/images/icn_cut.png" title="Cut">\
                       <img src="/static/ide/images/icn_copy.png" title="Copy">\
                       <img src="/static/ide/images/icn_paste.png" title="Paste">\
                       &nbsp;\
                       <img src="/static/ide/images/icn_undo.png" title="Undo">\
                       <img src="/static/ide/images/icn_redo.png" title="Redo">\
                     </div>'
    YAHOO.nagare.EditableSourceTab.superclass.constructor.call(this, info);

    // Add the actions on the icons
    // ----------------------------

    var icns = this.get('contentEl').getElementsByTagName('img');

    YAHOO.util.Event.addListener(icns[0], 'click', this.save, this, true);
    YAHOO.util.Event.addListener(icns[1], 'click', this.reload, this, true);

    YAHOO.util.Event.addListener(icns[2], 'click', function() { get_actions_manager().cutSelection(create_action_event()) });
    YAHOO.util.Event.addListener(icns[3], 'click', function() { get_actions_manager().copySelection(create_action_event()) });
    YAHOO.util.Event.addListener(icns[4], 'click', function() { get_actions_manager().pasteFromClipboard(create_action_event()) });

    YAHOO.util.Event.addListener(icns[5], 'click', function() { get_actions_manager().undo(create_action_event()) });
    YAHOO.util.Event.addListener(icns[6], 'click', function() { get_actions_manager().redo(create_action_event()) });

    this.pathname = info.pathname;

    this.source = "";
    this.modified = false;
    this.editor_state = null;
}

YAHOO.extend(YAHOO.nagare.EditableSourceTab, YAHOO.nagare.BaseTab, {
    resize: function(content, editor_id, editor) {
        // Method to resize the Bespin editor
        //
        // In:
        //   - ``content`` -- the YUI central panel object where the tabview is rendered
        // Get the central panel new dimensions
        var content_height = content.getSizes().body.h;
        var content_width = content.getSizes().body.w;

        // Resize the Bespin editor
        YAHOO.util.Dom.setStyle(editor_id, 'height', content_height-parseInt(tabview.getStyle('height'))-20+'px');
        YAHOO.util.Dom.setStyle(editor_id, 'width', content_width-4+'px');
    },

    onResize: function(content) {
        // Method called when the gobal layout is resized
        //
        // In:
        //   - ``content`` -- the YUI central panel object where the tabview is rendered
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object
        this.resize(content, 'editor', bespin.get('editor'));
    },

    onEnter: function(treeview, editor_id, editor) {
        // Focus on this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object
        YAHOO.nagare.EditableSourceTab.superclass.onEnter.call(this, treeview, editor_id, editor);

        // Resize the Bespin editor
        this.resize(layout.getUnitByPosition('center'), editor_id, editor);

        // And display it
        YAHOO.util.Dom.setStyle(editor_id, 'display', 'block');

        if(this.source == '') {
            // New tab without any source
            // Fetch the source from the server to he Bespin editor
            editor.openFile('Nagare', this.pathname, { reload: true });
        } else {
            // Tab already with a source content
            // Overwrite the content of the Bespin editor with it
            editor.model.insertDocument(this.source);
        }

        if(this.editor_state) {
            // Restore the cursor and selection state
            editor.setState(this.editor_state);
        }

        if(this.language) {
            // Restore the syntax highlighting type
            editor.language = this.language;
        }
    },

    onExit: function(treeview, editor_id, editor) {
        // Focus out of this tab
        //
        // In:
        //   - ``treeview`` -- the YUI tree view object
        //   - ``editor_id`` -- the Bespin editor DOM id
        //   - ``editor`` -- the Bespin editor object
        this.modified = this.isModified();          // Remember if the source was modified
        this.source = editor.model.getDocument();   // Keep the source out of the Bespin editor
        this.editor_state = editor.getState();      // Keep the cursor and selection state
        this.language = editor.language;            // Keep the syntax highlighting type

        // Hide the Bespin editor
        YAHOO.util.Dom.setStyle(editor_id, 'display', 'none');
    },

    isModified: function() {
        // Check is the source was modified since it was first loaded from the server
        //
        // Return:
        //   - a boolean
        return this.modified || (this.source != bespin.get('editor').model.getDocument());
    },

    save: function() {
        // Save the source to the server
        var tab = this;
        var editor = bespin.get('editor')
        editor.saveFile('Nagare', this.pathname, function() { tab.modified = false; tab.source = editor.model.getDocument() }, function() {});
    },

    close: function(tabview) {
        // Delete this tab
        //
        // In:
        //   - ``tabview`` -- the YUI treeview object
        var tab = this;
        var close = function() { YAHOO.nagare.EditableSourceTab.superclass.close.call(tab, tabview); }

        tabview.selectTab(tabview.getTabIndex(this));

        if(this.isModified()) {
            // Modified source, ask confirmation to close the tab
            confirm(close);
        } else {
            // Not modified source, close the tab
            close();
        }
    },

    reload: function() {
        // Reload the source from the server
        var tab = this;
        var editor = bespin.get('editor');
        var reload = function() { editor.model.clear(); editor.openFile('Nagare', tab.pathname, { reload: true }); }

        if(this.isModified()) {
            // Modified source, ask confirmation to reload the tab
            confirm(reload);
        } else {
            // Not modified source, reload the tab
            reload();
        }
    },

    set_line_number: function(lineno) {
        // Go to line
        //
        // In:
        //   - ``lineno`` -- the line number
        bespin.get('editor').moveAndCenter(lineno);
    }
});

// ----------------------------------------------------------------------------

YAHOO.nagare.ReadOnlySourceTab = function(info) {
    // Initialization
    //
    // In:
    //   - ``info.pathname`` -- complete pathname of the source file on the server
    //   - ``info.filename`` -- filename part of the pathname
    info.label = '<span title="' + info.pathname + '">' + info.filename + '</span>'

    id = 'id'+Math.ceil(Math.random()*1000000000);
    info.content =  '<div class=".highlight" id="' + id + '"/>'

    YAHOO.nagare.ReadOnlySourceTab.superclass.constructor.call(this, info);
    nagare_getAndEval('source/at/Nagare/'+info.pathname+'?id='+id);
}

YAHOO.extend(YAHOO.nagare.ReadOnlySourceTab, YAHOO.nagare.BaseTab, {
    set_line_number: function(lineno) {
        // Go to line
        //
        // In:
        //   - ``lineno`` -- the line number
    }
})

// ----------------------------------------------------------------------------

function on_file_opened(e) {
    // Function called after the Bespin editor has fetched a source from the server
    var tab = tabview.get('activeTab');

    if(tab) {
        tab.source = e.file.content;
        if(tab.line_number) {
            tab.set_line_number(tab.line_number);
        }
    }
}

function is_edition_supported() {
    return (YAHOO.env.ua.gecko || YAHOO.env.ua.webkit) && !!document.createElement('canvas').getContext;
}

function open_tab(data) {
    // Create or open a tab
    //
    // In:
    //   - ``data.uid`` -- UID of the tab to open
    var tabs = tabview.get('tabs');

    // Check if the tab is already opened
    for(var i=0; i<tabs.length; i++) {
        var tab = tabs[i];
        if(tab.uid == data.uid) {
            break;
        }
    }

    if(i == tabs.length) {
        // The tab doesn't yet exist. Create it
        var uid_parts = data.uid.split('@');

        if(uid_parts[0] == 'source') {
            // Create a Python source tab
            if(is_edition_supported()) {
                tab = new YAHOO.nagare.EditableSourceTab({ uid: data.uid, filename: data.filename, pathname: uid_parts[1] });
            } else {
                tab = new YAHOO.nagare.ReadOnlySourceTab({ uid: data.uid, filename: data.filename, pathname: uid_parts[1] });
            }
        }

        if(uid_parts[0] == 'exception') {
            // Create a Python exception tab
            tab = new YAHOO.nagare.ExceptionTab({ uid: data.uid, app: uid_parts[1] });
        }

        tabview.addTab(tab);

        if(data.lineno) {
            tab.line_number = data.lineno;
        }
    }

    // Put the focus on this new opened tab
    tabview.selectTab(tabview.getTabIndex(tab));

    if((i != tabs.length) && (data.lineno)) {
        tab.set_line_number(data.lineno);
    }
}

function setup_tree_view(treeview_id) {
    // Create the YUI tree view object
    //
    // In:
    //   - ``treeview_id`` -- the treeview container id
    var tree = new YAHOO.widget.TreeView(treeview_id);

    // A click on a tree element opens a tab
    tree.subscribe('clickEvent', function(e) { open_tab(e.node.data) });
    tree.render();

    return tree;
}

function setup_tab_view(tabview_id) {
    // Create the YUI tab view object
    //
    // In:
    //   - ``tabview_id`` -- the tabview container id
    var tabview = new YAHOO.widget.TabView(tabview_id);

    tabview.subscribe('activeTabChange', function(e) {
        if(e.prevValue) { e.prevValue.onExit(treeview, 'editor', bespin.get('editor')) }
        if(e.newValue) { e.newValue.onEnter(treeview, 'editor', bespin.get('editor')) }
    });

    return tabview;
}

function exceptions_tabs(exceptions) {
    // Refresh the exception tabs
    //
    // In:
    //   - ``exceptions`` -- list of applications where exceptions occured
    var tabs = tabview.get('tabs');

    // 1. Close all the old exception tabs
    for(var i=0; i<tabs.length; i++) {
        if(tabs[i].uid.match('^exception@')) {
            tabs[i].close(tabview);
        }
    }

    // 2. Create the new exception tabs
    for(var i=0; i<exceptions.length; i++) {
        var tab = new YAHOO.nagare.ExceptionTab({ uid: 'exception@'+exceptions[i], app: exceptions[i]});

        tabview.addTab(tab);
        tabview.selectTab(tabview.getTabIndex(tab));
    }
}

// ----------------------------------------------------------------------------

// Log functions
// -------------

function add_log(msg) {
    // Add a new log entry
    //
    // In:
    //   - ``msg`` -- a JSON list of the of entry parts
    var data = YAHOO.lang.JSON.parse(msg);

    var tr = document.createElement('tr');
    var tbody = document.getElementById('logs').children[1];

    // Insert the new entry at the beginning of the log
    if(!tbody.children.length) {
        tbody.appendChild(tr);
    } else {
        tbody.insertBefore(tr, tbody.firstChild);
    }

    for(var i=0; i<data.length; i++) {
        var td = document.createElement('td');
        td.appendChild(document.createTextNode(data[i]));
        tr.appendChild(td);
    }

    // Keep only the 10 newest entries
    while(tbody.children.length > 10) {
        tbody.removeChild(tbody.children[10]);
    }
}
