//--
// Copyright (c) 2008, 2009, 2010 Net-ng.
// All rights reserved.
//
// This software is licensed under the BSD License, as described in
// the file LICENSE.txt, which you should have received as part of
// this distribution.
//--

YAHOO.namespace('nagare');

YAHOO.nagare.BaseTab = function(info)
{
    info.label = info.label + ' <span title="close" class="tab_close"></span>';
    YAHOO.nagare.BaseTab.superclass.constructor.call(this, info);

    YAHOO.util.Event.on(this.getElementsByClassName('tab_close')[0], 'click', function(e, t) {
        t.close(tabview);
    }, this);

    this.uid = info.uid;
}

YAHOO.extend(YAHOO.nagare.BaseTab, YAHOO.widget.Tab, {
    onEnter: function(treeview, editor_id, editor) {
        var node = treeview.getNodeByProperty('uid', this.uid);
        if(node) {
            node.focus();
        }
    },

    onExit: function(treeview, editor_id, editor) {},
    onResize: function(content) {},

    close: function(tabview) {
        tabview.removeTab(this);
    }
});


YAHOO.nagare.ExceptionTab = function(info) {
    var div = document.getElementById('exception')
    if(div) {
        div.removeAttribute('id');
    }

    div = document.createElement('div');
    div.setAttribute('id', 'exception');
    document.getElementById('exceptions').appendChild(div);

    nagare_getAndEval('exception_tab/'+info.app);

    info.label = 'Exception in <i>' + info.app + '</i>'
    info.contentEl = div;

    YAHOO.nagare.SourceTab.superclass.constructor.call(this, info);
}

YAHOO.extend(YAHOO.nagare.ExceptionTab, YAHOO.nagare.BaseTab, {
    onEnter: function(treeview, editor_id, editor) {
        YAHOO.nagare.ExceptionTab.superclass.onEnter.call(this, treeview, editor_id, editor);

        YAHOO.util.Dom.setStyle(this.get('contentEl'), 'display', 'block');
    },

    onExit: function(treeview, editor_id, editor) {
        YAHOO.util.Dom.setStyle(this.get('contentEl'), 'display', 'none');
    }
});

function toto() {
    return { pos: bespin.editor.utils.copyPos(bespin.get('editor').cursorManager.getCursorPosition()) };
}

function titi() {
    return bespin.get('editor').ui.actions;
}

function confirm(action) {
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

YAHOO.nagare.SourceTab = function(info) {
    info.label = '<span title="' + info.pathname + '">' + info.filename + '</span>'
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
    YAHOO.nagare.SourceTab.superclass.constructor.call(this, info);

    var icns = this.get('contentEl').getElementsByTagName('img');

    YAHOO.util.Event.addListener(icns[0], 'click', this.save, this, true);
    YAHOO.util.Event.addListener(icns[1], 'click', this.reload, this, true);

    YAHOO.util.Event.addListener(icns[2], 'click', function() { titi().cutSelection(toto()) });
    YAHOO.util.Event.addListener(icns[3], 'click', function() { titi().copySelection(toto()) });
    YAHOO.util.Event.addListener(icns[4], 'click', function() { titi().pasteFromClipboard(toto()) });

    YAHOO.util.Event.addListener(icns[5], 'click', function() { titi().undo(toto()) });
    YAHOO.util.Event.addListener(icns[6], 'click', function() { titi().redo(toto()) });

    this.pathname = info.pathname;

    this.source = "";
    this.modified = false;
    this.editor_state = null;
}

YAHOO.extend(YAHOO.nagare.SourceTab, YAHOO.nagare.BaseTab, {
    resize: function(content, editor_id, editor) {;
        var content_height = content.getSizes().body.h;
        var content_width = content.getSizes().body.w;

        YAHOO.util.Dom.setStyle(editor_id, 'height', content_height-parseInt(tabview.getStyle('height'))-4+'px');
        YAHOO.util.Dom.setStyle(editor_id, 'width', content_width-4+'px');
    },

    onResize: function(content) {
        this.resize(content, 'editor', bespin.get('editor'));
    },

    onEnter: function(treeview, editor_id, editor) {
        YAHOO.nagare.SourceTab.superclass.onEnter.call(this, treeview, editor_id, editor);

        this.resize(layout.getUnitByPosition('center'), editor_id, editor);

        YAHOO.util.Dom.setStyle(editor_id, 'display', 'block');

        //editor.model.clear();

        if(this.source == '') {
            editor.openFile('Nagare', this.pathname, { reload: true });
        } else {
            editor.model.insertDocument(this.source);
        }

        if(this.editor_state) {
            editor.setState(this.editor_state);
        }
    },

    onExit: function(treeview, editor_id, editor) {
        this.modified = this.isModified();
        this.source = editor.model.getDocument();
        this.editor_state = editor.getState();

        YAHOO.util.Dom.setStyle(editor_id, 'display', 'none');
    },

    isModified: function() {
        return this.modified || (this.source != bespin.get('editor').model.getDocument());
    },

    save: function() {
        var tab = this;
        var editor = bespin.get('editor')
        editor.saveFile('Nagare', this.pathname, function() { tab.modified = false; tab.source = editor.model.getDocument() }, function() {});
    },

    close: function(tabview) {
        var tab = this;
        var close = function() { YAHOO.nagare.SourceTab.superclass.close.call(tab, tabview); }

        tabview.selectTab(tabview.getTabIndex(this));

        if(this.isModified()) {
            confirm(close);
        } else {
            close();
        }
    },

    reload: function() {
        var tab = this;
        var editor = bespin.get('editor');
        var reload = function() { editor.model.clear(); editor.openFile('Nagare', tab.pathname, { reload: true }); }

        if(this.isModified()) {
            confirm(reload);
        } else {
            reload();
        }
    },

    set_line_number: function(lineno) {
        bespin.get('editor').moveAndCenter(lineno);
    }

});

function onFileOpened(e) {
    var tab = tabview.get('activeTab');

    if(tab) {
        tab.source = e.file.content;
    }
}

// ----------------------------------------------------------------------------

function open_tab(data) {
    var tabs = tabview.get('tabs');

    for(var i=0; i<tabs.length; i++) {
        var tab = tabs[i];
        if(tab.uid == data.uid) {
            break;
        }
    }

    if(i == tabs.length) {
        var uid_parts = data.uid.split('@');

        if(uid_parts[0] == 'source')
        {
            tab = new YAHOO.nagare.SourceTab({ uid: data.uid, filename: data.filename, pathname: uid_parts[1] });
        }

        if(uid_parts[0] == 'exception')
        {
            tab = new YAHOO.nagare.ExceptionTab({ uid: data.uid, content_id: 'toto', app: uid_parts[1]});
        }

        tabview.addTab(tab);
    }

    tabview.selectTab(tabview.getTabIndex(tab));

    if(data.lineno) {
        tab.set_line_number(data.lineno);
    }
}

function setupTreeView(treeview_id)
{
    var tree = new YAHOO.widget.TreeView(treeview_id);

    tree.subscribe('clickEvent', function(e) { open_tab(e.node.data) });
    tree.render();

    return tree;
}

function setupTabView(tabview_id)
{
    var tabview = new YAHOO.widget.TabView(tabview_id);

    tabview.subscribe('activeTabChange', function(e) {
        if(e.prevValue) { e.prevValue.onExit(treeview, 'editor', bespin.get('editor')) }
        if(e.newValue) { e.newValue.onEnter(treeview, 'editor', bespin.get('editor')) };
    });

    return tabview;
}

function exceptions_tabs(exceptions)
{
    var tabs = tabview.get('tabs');

    for(var i=0; i<tabs.length; i++) {
        if(tabs[i].uid.match('^exception@')) {
            tabs[i].close(tabview);
        }
    }

    for(var i=0; i<exceptions.length; i++) {
        var tab = new YAHOO.nagare.ExceptionTab({ uid: 'exception@'+exceptions[i], content_id: 'toto', app: exceptions[i]});
        tabview.addTab(tab);
        tabview.selectTab(tabview.getTabIndex(tab));
    }
}

// ----------------------------------------------------------------------------

function add_log(msg) {
    var line = document.createElement('tr');
    var tbody = document.getElementById('logs').children[1];

    if(!tbody.children.length) {
        tbody.appendChild(line);
    } else {
        tbody.insertBefore(line, tbody.firstChild)
    }

    line.innerHTML = msg;

    while(tbody.children.length > 10) {
        tbody.removeChild(tbody.children[10]);
    }
}

// ----------------------------------------------------------------------------

function dispatch(msg) {
    if(msg.match('^nagare_updateNode')) {
        eval(msg);
    }
}
