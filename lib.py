__author__ = "siznax"
__version__ = 2014

import datetime
import markdown
import os
import re
import sqlite3
import string
import sys
import urlparse

from flask import render_template, request, redirect, url_for, Markup


class Tanuki:

    MAX_TITLE_LEN = 80
    MAX_ENTRY_LEN = 131072

    def __init__(self, config):
        self.config = config
        self.DEBUG = config['DEBUG']
        self.editing = False
        self.mode = None
        if self.DEBUG:
            print self.config

    def connect(self):
        dbfile = os.path.join(os.path.dirname(__file__), "tanuki.db")
        if request.path.startswith('/help'):
            dbfile = os.path.join(os.path.dirname(__file__), "help.db")
        if self.DEBUG:
            print "+ TANUKI connecting to %s" % (dbfile)
        self.con = sqlite3.connect(dbfile)
        self.con.execute('pragma foreign_keys = on')  # !important
        self.db = self.con.cursor()
        self.dbfile = dbfile

    def dbquery(self, sql, val=''):
        msg = "+ TANUKI SQL: %s" % (sql)
        if val:
            msg += " VAL: %s" % (''.join(str(val)))
        result = self.db.execute(sql, val)
        if self.DEBUG:
            print msg
        return result

    def num_entries(self):
        sql = 'select count(*) from entries'
        val = ''
        return self.dbquery(sql, val).fetchone()[0]

    def tag_set(self):
        sql = 'select count(*),name from tags group by name order by name'
        val = ''
        return [{'count': r[0], 'name': r[1]} for r in self.dbquery(sql, val)]

    def tag_set_msg(self):
        entries_msg = "%d entries" % self.num_entries()
        tags_msg = "%d tags" % len(self.tag_set())
        notag = len(self.entries(None, True))
        notag_msg = ""
        if notag:
            notag_msg = '(%d <a href="/notag">notag</a>)' % notag
            return "%s %s %s" % (entries_msg, tags_msg, notag_msg)
        return "%s: %s" % (entries_msg, tags_msg)

    def tag_hrefs(self, tag_set, br=False):
        hrefs = []
        for t in tag_set:
            href = "<a href=\"/tagged/%s\"># %s</a>" % (t, t)
            hrefs.append(href)
        if br:
            return "<br />".join(hrefs)
        return " ".join(hrefs)

    def div(self, _id, _class, href=None):
        onclick = 'onclick="window.location=\'%s\';"' % href if href else ''
        return '<div id="%s" class="%s" %s></div>' % (
            _id, _class or '', onclick)

    def img(self, alt, href=None):
        img = '<img id="%s" alt="%s" src="/static/%s.png">'\
            % (alt, alt,  alt)
        if href:
            return '<a href="%s">%s</a>' % (href, img)
        else:
            return img

    def new(self):
        date = datetime.date.today().isoformat()
        n = {'date': date,
             'text': 'text',
             'title': 'title',
             'tags': 'tags',
             'public': 0}
        controls = ['home', 'list', 'tags', 'search']
        return render_template('edit.html',
                               entry=n,
                               controls=self.controls(0, controls),
                               title='new entry',
                               body_class='edit')

    def edit(self, entry_id):
        self.mode = 'edit'
        entry = self.entry(entry_id, False, None, True)
        referrer = request.referrer
        if not referrer:
            referrer = "/entry/%s" % entry_id
        controls = ['home', 'list', 'tags', 'search', 'new']
        title = "edit %s: %s" % (entry_id, entry['title'])
        return render_template('edit.html',
                               entry=entry,
                               referrer=referrer,
                               title=title,
                               controls=self.controls(0, controls),
                               body_class=self.mode)

    def clear_tags(self, entry_id):
        self.dbquery("delete from tags where id=?", [entry_id])

    def norm_tags(self, blob):
        norm = []
        # lower, strip, split, unique
        for tag in set(''.join(blob.lower().split()).split(',')):
            # remove punctuation
            exclude = set(string.punctuation)
            norm.append(''.join(ch for ch in tag if ch not in exclude))
        return norm

    def store_tags(self, entry_id, tags):
        self.clear_tags(entry_id)
        if not tags or tags == 'tags':
            return
        count = 0
        for tag in self.norm_tags(tags):
            if count > 5:
                return
            sql = 'insert into tags values(?,?,?)'
            date = datetime.date.today().isoformat()
            self.dbquery(sql, [entry_id, tag[:32], date])
            count += 1

    def bad_str(self, instr):
        # disallow INT only
        try:
            type(int(instr))
            return True
        except ValueError:
            return False

    def upsert(self, req):
        self.environ = req.environ
        try:
            datetime.datetime.strptime(req.form['date'], '%Y-%m-%d')
            if 'locked' in req.form:
                raise ValueError
            if self.bad_str(req.form['title']):
                raise ValueError
            if self.bad_str(req.form['entry']):
                raise ValueError
            if 'entry_id' in req.form.keys():
                sql = 'update entries set '\
                    'title=?,text=?,date=?,updated=?,public=? '\
                    'where id=?'
                val = (req.form['title'][:Tanuki.MAX_TITLE_LEN],
                       req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
                       req.form['date'],
                       self.utcnow(),
                       0,
                       req.form['entry_id'])
                self.dbquery(sql, val)
                entry_id = req.form['entry_id']
            else:
                sql = 'insert into entries values(?,?,?,?,?,?)'
                val = [None,
                       req.form['title'][:Tanuki.MAX_TITLE_LEN],
                       req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
                       req.form['date'],
                       self.utcnow(),
                       0]
                cur = self.dbquery(sql, val)
                entry_id = cur.lastrowid

            self.store_tags(entry_id, req.form['tags'])
            self.con.commit()

            url = "%s/entry/%s" % (self.environ['HTTP_ORIGIN'], entry_id)
            ref = req.form['referrer'] if 'referrer' in req.form else url
            return redirect(ref)
        except ValueError:
            msg = "ValueError raised, try again."
            return render_template('error.html', msg=msg)
        except sqlite3.IntegrityError:
            msg = "Try again, title or text not unique."
            return render_template('error.html', msg=msg)

    def confirm(self, entry_id):
        entry = self.entry(entry_id)
        return render_template('confirm.html', entry=entry, func='destroy')

    def delete(self, entry_id):
        self.clear_tags(entry_id)
        self.dbquery('DELETE from entries WHERE id=?', [entry_id])
        self.con.commit()

    def get_tags(self, eid):
        t = []
        for r in self.dbquery('select name from tags where id=?', [eid]):
            t.append(r[0])
        return sorted(t)

    def apply_tags(self, entries):
        for x in entries:
            tags = self.get_tags(x['id'])
            x['tags'] = ', '.join(tags) if self.editing else tags
        return entries

    def utcdate(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

    def utcnow(self):
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")

    def date_str(self, date):
        try:
            return datetime.datetime.strptime(
                date, '%Y-%m-%d').strftime('%a %d %b %Y')
        except:
            return 'MALFORMED'

    def ymd(self, date):
        parsed = datetime.datetime.strptime(date, '%Y-%m-%d')
        return [parsed.strftime('%Y'),
                parsed.strftime('%b'),
                parsed.strftime('%d')]

    def demux(self, row):
        # overevaluated, don't try to do much here
        ymd = self.ymd(row[3])
        text = None
        if request.path.startswith('/confirm')\
                or request.path.startswith('/edit')\
                or request.path.startswith('/entry')\
                or request.path.startswith('/help')\
                or request.path.startswith('/store')\
                or request.path.startswith('/tagged'):
            text = row[2]
        return {'id': row[0],
                'title': row[1],
                'text': text,
                'date': row[3],
                'updated': row[4],
                'public': row[5],
                'year': ymd[0],
                'month': ymd[1],
                'date_str': self.date_str(row[3]),
                'mediatype': 'text'}

    def markdown(self, entry_id, text):
        if self.DEBUG:
            print "+ TANUKI markdown %d %d bytes"\
                % (entry_id, sys.getsizeof(text))
        return markdown.markdown(text)

    def markup(self, entries):  # Warning! this can be expensive
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI markup %d %d bytes"\
                    % (x['id'], sys.getsizeof(x['text']))
            x['text'] = markdown.markdown(x['text'])
        return entries

    def controls(self, entry_id, wanted=None):
        delete = self.img('delete', "/confirm/%d" % (entry_id))
        edit_href = "/edit/%d" % (entry_id)
        entry_href = "/entry/%d" % (entry_id)
        if request.path.startswith('/help'):
            delete = ''
            edit_href = "/help/edit/%d" % (entry_id)
        if '/entry' in request.path:
            entry_href = ''
        c = {'home': self.img('home', '/'),
             'new': self.img('new', '/new'),
             'entry': self.img('entry', entry_href),
             'edit': self.img('edit', edit_href),
             'delete': delete,
             'list': self.img('list', '/list'),
             'tags': self.img('tags', '/tags'),
             'search': self.img('search', '/search'),
             'help': self.img('help', '/help')}
        s = "\n"
        for w in wanted:
            s += "%s\n" % (c[w])
        return s

    def href2img(self, href, alt):
        img = '<img alt="%s" title="%s" src="%s">' % (alt, alt, href)
        return '<a href="%s">%s</a>' % (href, img)

    def preprocess(self, entries):  # before markdown
        if self.editing:
            return entries
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI preprocess %d" % (x['id'])
            if x['text'].startswith('http'):
                x['mediatype'] = 'img'
                text = x['text'].strip()
                lines = text.split("\n")
                first_line = lines[0].strip()
                # convert URL to <img>
                img_tag = self.href2img(first_line, x['title'])
                x['text'] = "%s\n%s" % (img_tag, "\n".join(lines[1:]))
            if re.match(r'^<video|<iframe|<object', x['text']):
                x['mediatype'] = 'video'
        return entries

    def postprocess(self, entries):  # AFTER markdown
        if self.editing:
            return entries
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI postprocess %d" % (x['id'])
            x['img'] = self.find_img(x['text'])
        return entries

    def entry(self, entry_id, markup=False, title=None, editing=False):
        if editing:
            self.editing = True
        if title:
            sql = 'select * from entries where title=?'
            row = self.dbquery(sql, [title]).fetchone()
        else:
            sql = 'select * from entries where id=?'
            row = self.dbquery(sql, [entry_id]).fetchone()
        if not row:
            return None
        entries = [self.demux(row)]
        entries = self.apply_tags(entries)
        entries = self.preprocess(entries)
        if markup:
            entries = self.markup(entries)
        self.editing = False
        return entries[0]

    def entries_tagged(self, tag):
        sql = 'select * from entries,tags '\
            'where tags.name=? and tags.id=entries.id '\
            'order by date desc'
        return [self.demux(x) for x in self.dbquery(sql, [tag])]

    def entries_notag(self):
        sql = 'select * from entries where id not in (select id from tags)'
        val = ''
        return [self.demux(x) for x in self.dbquery(sql, val)]

    def entries_matching(self, terms):
        sql = 'select * from entries '\
            'where title like ? or text like ? '\
            'order by id desc'
        val = [terms, terms]
        return [self.demux(x) for x in self.dbquery(sql, val)]

    def entries_latest(self):
        sql = 'select * from entries order by updated desc limit 10'
        val = ''
        return [self.demux(x) for x in self.dbquery(sql, val)]

    def entries(self, tag=None, notag=False, terms=None, latest=None):
        if "help.db" in self.dbfile:
            sql = 'select * from entries'
            return [self.demux(x) for x in self.dbquery(sql)]
        if tag:
            entries = self.entries_tagged(tag)
        elif notag:
            entries = self.entries_notag()
        elif terms:
            terms = '%' + terms.encode('ascii', 'ignore') + '%'
            entries = self.entries_matching(terms)
        elif latest:
            entries = self.entries_latest()
        else:
            sql = 'select * from entries order by date desc,id desc'
            val = ''
            entries = [self.demux(x) for x in self.dbquery(sql, val)]
        if self.DEBUG:
            print "+ TANUKI entries %d bytes" % (sys.getsizeof(entries))
        return entries

    def index(self, page=0):
        latest = self.entries(None, False, None, True)
        readme = self.entries_tagged("readme")
        controls = ['home', 'list', 'tags', 'search', 'new', 'help']
        return render_template('index.html',
                               controls=self.controls(0, controls),
                               latest=latest,
                               readme=readme,
                               tag_set=self.tag_set(),
                               body_class='index',
                               msg=self.tag_set_msg())

    def help(self):
        controls = self.controls(0, ['home', 'list', 'tags', 'search', 'new'])
        return render_template("help.html",
                               controls=controls,
                               entries=self.entries(),  # connected to help.db
                               title="help",
                               body_class="help")

    def find_img(self, html):
        if not html:
            return None
        import lxml.html
        doc = lxml.html.document_fromstring(html)
        for src in doc.xpath("//img/@src"):
            return src

    def iframe_src(self, text):
        src = re.search(r'src="([^"]*)"', text)
        if src:
            return src.groups()[0]
        src = re.search(r"src='([^']*)'", text)
        if src:
            return src.groups()[0]
        return None

    def iframe_stub(self, text):
        stub = 'IFRAME STUB'
        src = self.iframe_src(text)
        if src:
            url = urlparse.urlparse(src)
            stub = '{ <a href="%s">%s</a> }' % (src, url.netloc)
        return re.sub(r'<iframe.*iframe>', stub, text)

    def strip_tags(self, html):
        if not html:
            return None
        return Markup(html).striptags()

    # DEPRECATED: things done here should set members of each
    # entry in postprocessing. then let the template use them.
    def grid_cells(self, entries):
        for x in entries:
            if x['mediatype'] == 'text':
                # strip tags and extract img src
                html = self.markdown(x['id'], x['text'])
                x['img'] = self.find_img(html)
                x['text'] = self.strip_tags(html)
            if x['mediatype'] == 'video':
                x['text'] = self.iframe_stub(x['text'])
        return entries

    def result_words(self, total, from_to=None):
        if (from_to):
            return "%s of %d entries" % (from_to, total)
        else:
            return "%d entries" % (total)

    def list(self):
        entries = self.entries()  # consider removing text
        controls = self.controls(0, ['home', 'tags', 'search', 'new'])
        if not entries:
            msg = "<h3>Unbelievable. No entries yet.</h3>"
        else:
            msg = self.result_words(len(entries))
        return render_template('list.html',
                               msg=msg,
                               controls=controls,
                               entries=entries)

    def singleton(self, entry_id):
        self.mode = 'entry'
        entry = self.entry(entry_id, True)
        if not entry:
            return redirect(url_for('index'))
        controls = ['home', 'list', 'tags', 'search', 'new', 'edit', 'delete']
        return render_template('entry.html',
                               controls=self.controls(entry_id, controls),
                               next_prev=None,
                               entry=entry,
                               title=entry['title'],
                               body_class="entry")

    def tagged_view_msg(self, tag, view):
        if view:
            a1 = '<a href="/tagged/%s">list</a>' % (tag)
        else:
            a1 = '<b>list</b>'
        if view == 'gallery':
            a2 = '<b>gallery</b>'
        else:
            a2 = '<a href="/tagged/%s/v:gallery">gallery</a>' % (tag)
        return ' | '.join([a1, a2])

    def tagged(self, tag, view=None):
        self.mode = None
        haztag = self.entries(tag)
        haztag = self.apply_tags(haztag)
        haztag = self.preprocess(haztag)
        haztag = self.markup(haztag)
        haztag = self.postprocess(haztag)
        controls = ['home', 'list', 'tags', 'search', 'new']
        title = "%d #%s" % (len(haztag), tag)
        msg = "%s %s" % (title, self.tagged_view_msg(tag, view))
        return render_template('list.html' if not view else 'gallery.html',
                               msg=msg,
                               controls=self.controls(0, controls),
                               title=title,
                               entries=haztag)

    def tags(self):
        self.mode = None
        tag_set = self.tag_set()
        title = "%d tags" % len(tag_set)
        msg = "<h3>Unbelievable. No tags yet.</h3>"
        if tag_set:
            msg = self.tag_set_msg()
        controls = self.controls(0, ['home', 'list', 'search', 'new'])
        return render_template('tags.html',
                               title=title,
                               msg=msg,
                               controls=controls,
                               tag_set=tag_set)

    def notag(self):
        self.mode = None
        untagged = self.entries(None, True)
        controls = ['home', 'list', 'tags', 'search', 'new']
        title = "%d notag" % len(untagged)
        msg = "%d not tagged" % len(untagged)
        return render_template('list.html',
                               title=title,
                               msg=msg,
                               controls=self.controls(0, controls),
                               entries=untagged)

    def search(self):
        controls = self.controls(0, ['home', 'list', 'tags', 'new'])
        return render_template('search.html',
                               controls=controls)

    def found(self, terms):
        self.mode = None
        found = self.entries(None, False, terms)
        controls = ['home', 'list', 'tags', 'search', 'new']
        msg='found (%d) matching "%s"' % (len(found), terms)
        return render_template('list.html',
                               msg = msg,
                               controls=self.controls(0, controls),
                               entries=found)
