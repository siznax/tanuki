__author__ = "siznax"
__version__ = 2014

import datetime
import markdown
import os
import re
import sqlite3
import string
import sys

from flask import render_template, request, redirect, abort


class Tanuki:

    MAX_TITLE_LEN = 80
    MAX_ENTRY_LEN = 131072

    def __init__(self, config):
        self.DEBUG = config['DEBUG']
        self.config = config
        if self.DEBUG:
            print self.config

    def db_connect(self):
        dbfile = os.path.join(os.path.dirname(__file__), "tanuki.db")
        if request.path.startswith('/help'):
            dbfile = os.path.join(os.path.dirname(__file__), "help.db")
        self.dbfile = dbfile
        if self.DEBUG:
            print "+ TANUKI connecting to %s" % (dbfile)
        self.con = sqlite3.connect(dbfile)
        self.con.execute('pragma foreign_keys = on')  # !important
        self.db = self.con.cursor()

    def db_query(self, sql, val=''):
        result = self.db.execute(sql, val)
        if self.DEBUG:
            msg = "+ TANUKI SQL: %s" % (sql)
            if val:
                msg += " VAL: %s" % (''.join(str(val)))
            print msg
        return result

    def get_num_entries(self):
        """returns count of entries table."""
        sql = 'select count(*) from entries'
        val = ''
        return self.db_query(sql, val).fetchone()[0]

    def get_status(self):
        """get and set status data, mostly counts."""
        self.num_entries = self.get_num_entries()
        self.num_tags = len(self.get_tag_set())
        self.num_notag = len(self.get_notag_entries())

    def get_status_msg(self):
        """return interface status string."""
        self.get_status()
        return " ".join([str(self.num_entries), "entries",
                         str(self.num_tags), "tags",
                         str(self.num_notag), '<a href="/notag">notag</a>'])

    def render_new_form(self):
        entry = {'date': datetime.date.today().isoformat(),
                 'text': 'text',
                 'title': 'title',
                 'tags': 'tags',
                 'public': 0}
        controls = ['home', 'list', 'tags', 'search', 'help']
        return render_template('edit.html',
                               entry=entry,
                               controls=self.controls(0, controls),
                               title='new entry',
                               body_class='edit')

    def render_edit_form(self, entry_id):
        entry = self.get_entry(entry_id, True)
        referrer = request.referrer
        if not referrer:
            referrer = "/entry/%s" % entry_id
        controls = ['home', 'list', 'tags', 'search', 'new', 'help']
        title = "edit %s: %s" % (entry_id, entry['title'])
        return render_template('edit.html',
                               entry=entry,
                               referrer=referrer,
                               title=title,
                               controls=self.controls(0, controls),
                               body_class='edit')

    def clear_tags(self, entry_id):
        self.db_query("delete from tags where id=?", [entry_id])

    def store_tags(self, entry_id, tags):
        self.clear_tags(entry_id)
        if not tags or tags == 'tags':
            return
        count = 0
        for tag in normalize_tags(tags):
            if count > 5:
                return
            sql = 'insert into tags values(?,?,?)'
            date = datetime.date.today().isoformat()
            self.db_query(sql, [entry_id, tag[:32], date])
            count += 1

    def upsert(self, req):
        self.environ = req.environ
        try:
            datetime.datetime.strptime(req.form['date'], '%Y-%m-%d')
            if 'locked' in req.form:
                raise ValueError
            if str_is_int(req.form['title']):
                raise ValueError
            if str_is_int(req.form['entry']):
                raise ValueError
            if 'entry_id' in req.form.keys():
                sql = 'update entries set '\
                    'title=?,text=?,date=?,updated=?,public=? '\
                    'where id=?'
                val = (req.form['title'][:Tanuki.MAX_TITLE_LEN],
                       req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
                       req.form['date'],
                       utcnow(),
                       0,
                       req.form['entry_id'])
                self.db_query(sql, val)
                entry_id = req.form['entry_id']
            else:
                sql = 'insert into entries values(?,?,?,?,?,?)'
                val = [None,
                       req.form['title'][:Tanuki.MAX_TITLE_LEN],
                       req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
                       req.form['date'],
                       utcnow(),
                       0]
                cur = self.db_query(sql, val)
                entry_id = cur.lastrowid

            self.store_tags(entry_id, req.form['tags'])
            self.con.commit()

            url = "%s/entry/%s" % (self.environ['HTTP_ORIGIN'], entry_id)
            ref = req.form['referrer'] if 'referrer' in req.form else url
            return redirect(ref)
        except ValueError:
            return render_template('error.html',
                                   msg="ValueError raised, try again.")
        except sqlite3.IntegrityError:
            return render_template('error.html',
                                   msg="Title or text not unique, try again.")

    def delete(self, entry_id):
        self.clear_tags(entry_id)
        self.db_query('DELETE from entries WHERE id=?', [entry_id])
        self.con.commit()

    def render_confirm_form(self, entry_id):
        return render_template('confirm.html',
                               entry=self.get_entry(entry_id),
                               func='destroy')

    def get_tags(self, eid):
        """return sorted list of tag names."""
        t = []
        for r in self.db_query('select name from tags where id=?', [eid]):
            t.append(r[0])
        return sorted(t)

    def apply_tags(self, entries, editing=False):
        for x in entries:
            tags = self.get_tags(x['id'])
            if editing:
                x['tags'] = ', '.join(str(x) for x in tags)
            else:
                x['tags'] = tags
        return entries

    def demux(self, row):
        # overevaluated, don't try to do much here
        ymd = parse_ymd(row[3])
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
                'date_str': date_str(row[3]),
                'mediatype': 'text'}

    def markdown_entries(self, entries):  # Warning! this can be expensive
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI markdown %d %d bytes"\
                    % (x['id'], sys.getsizeof(x['text']))
            x['text'] = markdown.markdown(x['text'])
        return entries

    def controls(self, entry_id, wanted=None):
        """compute UI "buttons" string."""
        delete = ui_img('delete', "/confirm/%d" % (entry_id))
        edit_href = "/edit/%d" % (entry_id)
        entry_href = "/entry/%d" % (entry_id)
        if request.path.startswith('/help'):
            delete = ''
            edit_href = "/help/edit/%d" % (entry_id)
        if '/entry' in request.path:
            entry_href = ''
        btns = {'home': ui_img('home', '/'),
                'new': ui_img('new', '/new'),
                'entry': ui_img('entry', entry_href),
                'edit': ui_img('edit', edit_href),
                'delete': delete,
                'list': ui_img('list', '/list'),
                'tags': ui_img('tags', '/tags'),
                'search': ui_img('search', '/search'),
                'help': ui_img('help', '/help')}
        _str = "\n"
        for wtd in wanted:
            _str += "%s\n" % (btns[wtd])
        return _str

    def href2img(self, href, alt):
        img = '<img alt="%s" title="%s" src="%s">' % (alt, alt, href)
        return '<a href="%s">%s</a>' % (href, img)

    def pre_markdown(self, entries):
        """pre-markdown needful operations."""
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI pre_markdown %d" % (x['id'])
            if re.match(r'^<video|<iframe|<object', x['text']):
                x['mediatype'] = 'video'
        return entries

    def find_img(self, html):
        if not html:
            return None
        import lxml.html
        doc = lxml.html.document_fromstring(html)
        for src in doc.xpath("//img/@src"):
            return src

    def post_markdown(self, entries):
        """post-markdown needful operations."""
        for x in entries:
            if self.DEBUG:
                print "+ TANUKI post_markdown %d" % (x['id'])
            x['img'] = self.find_img(x['text'])
        return entries

    def get_latest_entries(self):
        """return last ten entries updated."""
        sql = 'select * from entries order by updated desc limit 10'
        val = ''
        return [self.demux(x) for x in self.db_query(sql, val)]

    def render_index(self, page=0):
        readme = self.get_entries_tagged("readme")
        controls = ['home', 'list', 'tags', 'search', 'new', 'help']
        msg = self.get_status_msg()
        return render_template('index.html',
                               msg=msg,
                               title=self.num_entries,
                               controls=self.controls(0, controls),
                               latest=self.get_latest_entries(),
                               readme=readme,
                               tag_set=self.get_tag_set(),
                               body_class='index')

    def get_entries(self):
        """return fully hydrated entries ordered by date."""
        sql = 'select * from entries order by date desc,id desc'
        val = ''
        entries = [self.demux(x) for x in self.db_query(sql, val)]
        if self.DEBUG:
            print "+ TANUKI entries %d bytes" % (sys.getsizeof(entries))
        return entries

    def render_list(self):
        entries = self.get_entries()  # consider removing text
        controls = ['home', 'tags', 'search', 'new', 'help']
        return render_template('list.html',
                               title="list (%d)" % len(entries),
                               msg=self.get_status_msg(),
                               controls=self.controls(0, controls),
                               entries=entries)

    def get_entry(self, entry_id, editing=False):
        """returns single entry as HTML or markdown text."""
        sql = 'select * from entries where id=?'
        row = self.db_query(sql, [entry_id]).fetchone()
        if not row:
            abort(404)
        entry = [self.demux(row)]
        entry = self.apply_tags(entry, editing)
        if not editing:
            entry = self.pre_markdown(entry)
            entry = self.markdown_entries(entry)
        return entry[0]

    def render_entry(self, entry_id):
        entry = self.get_entry(entry_id)
        controls = ['home', 'list', 'tags', 'search', 'new', 'edit',
                    'delete', 'help']
        return render_template('entry.html',
                               controls=self.controls(entry_id, controls),
                               entry=entry,
                               title=entry['title'],
                               body_class="entry")

    def get_tag_set(self):
        """return dict of tag names keyed on count."""
        sql = 'select count(*),name from tags group by name order by name'
        val = ''
        return [{'count': r[0], 'name': r[1]} for r in self.db_query(sql, val)]

    def render_tags(self):
        tag_set = self.get_tag_set()
        title = "%d tags" % len(tag_set)
        controls = ['home', 'list', 'search', 'new', 'help']
        return render_template('tags.html',
                               title=title,
                               msg=self.get_status_msg(),
                               controls=self.controls(0, controls),
                               tag_set=tag_set)

    def msg_options(self, tag, view='list'):  # TODO: poor implementation
        opt1 = '<b>list</b>'
        opt2 = '<a href="/tagged/%s/v:gallery">gallery</a>' % (tag)
        if view == 'gallery':
            opt1 = '<a href="/tagged/%s">list</a>' % (tag)
            opt2 = '<b>gallery</b>'
        return " &mdash; " + ' | '.join([opt1, opt2])

    def get_entries_tagged(self, tag):
        """return entries matching tag name ordered by date."""
        sql = 'select * from entries,tags '\
            'where tags.name=? and tags.id=entries.id '\
            'order by date desc'
        return [self.demux(x) for x in self.db_query(sql, [tag])]

    def render_tagged(self, tag, view=None):
        tagged = self.get_entries_tagged(tag)
        tagged = self.apply_tags(tagged)
        tagged = self.pre_markdown(tagged)
        tagged = self.markdown_entries(tagged)
        tagged = self.post_markdown(tagged)
        num = len(tagged)
        controls = ['home', 'list', 'tags', 'search', 'new', 'help']
        title = "#%s (%d)" % (tag, num)
        msg = '%d tagged "%s" %s' % (num, tag, self.msg_options(tag, view))
        template = 'list.html' if not view else 'gallery.html'
        return render_template(template,
                               msg=msg,
                               controls=self.controls(0, controls),
                               title=title,
                               entries=tagged)

    def get_notag_entries(self):
        """return entries having no tags."""
        sql = 'select * from entries where id not in (select id from tags)'
        val = ''
        return [self.demux(x) for x in self.db_query(sql, val)]

    def render_notags(self):
        untagged = self.get_notag_entries()
        controls = ['home', 'list', 'tags', 'search', 'new']
        msg = "%d not tagged" % len(untagged)
        return render_template('list.html',
                               title=msg,
                               msg=msg,
                               controls=self.controls(0, controls),
                               entries=untagged)

    def render_search_form(self):
        controls = ['home', 'list', 'tags', 'new', 'help']
        return render_template('search.html',
                               controls=self.controls(0, controls))

    def get_entries_matching(self, terms):
        """return entries matching terms in title or text."""
        terms = '%' + terms.encode('ascii', 'ignore') + '%'
        sql = 'select * from entries '\
            'where title like ? or text like ? '\
            'order by id desc'
        val = [terms, terms]
        return [self.demux(x) for x in self.db_query(sql, val)]

    def found(self, terms):
        found = self.get_entries_matching(terms)
        controls = ['home', 'list', 'tags', 'search', 'new']
        msg = 'found (%d) matching "%s"' % (len(found), terms)
        return render_template('list.html',
                               msg=msg,
                               controls=self.controls(0, controls),
                               entries=found)

    def get_help_entries(self):
        """return entries from help.db."""
        sql = 'select * from entries'
        return [self.demux(x) for x in self.db_query(sql)]

    def render_help(self):
        controls = ['home', 'list', 'tags', 'search', 'new']
        return render_template("help.html",
                               controls=self.controls(0, controls),
                               entries=self.get_help_entries(),
                               title="help",
                               body_class="help")


def date_str(date):
    """return "Mon 1 Jan 1970" from 'YYYY-mm-dd'."""
    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%a %d %b %Y')
    except:
        return 'MALFORMED'


def normalize_tags(blob):
    norm = []
    # lower, strip, split, unique
    for tag in set(''.join(blob.lower().split()).split(',')):
        # remove punctuation
        exclude = set(string.punctuation)
        norm.append(''.join(ch for ch in tag if ch not in exclude))
    return norm


def parse_ymd(date):
    """return [y, m, d] from 'YYYY-mm-dd'"""
    parsed = datetime.datetime.strptime(date, '%Y-%m-%d')
    return [parsed.strftime('%Y'),
            parsed.strftime('%b'),
            parsed.strftime('%d')]


def str_is_int(_str):
    """return True if string is merely an integer."""
    try:
        type(int(_str))
        return True
    except ValueError:
        return False


def ui_img(alt, href=None):
    """return img tag given UI key (by convention)."""
    img = '<img id="%s" alt="%s" src="/static/%s.png">' % (alt, alt, alt)
    if href:
        return '<a href="%s">%s</a>' % (href, img)
    else:
        return img


def utcnow():
    """return simpler ISO 8601 date string."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
