__author__ = "siznax"
__date__ = "Jan 2015"

import datetime
import logging
import markdown
import os
import re
import sqlite3
import string
import sys

from flask import render_template, request, redirect, abort


class Tanuki:

    DEFAULT_DB = "tanuki.db"
    DEFAULT_HELP_DB = "help.db"
    MAX_ENTRY_LEN = 131072
    MAX_TAGS_PER_ENTRY = 5
    MAX_TAG_LEN = 32
    MAX_TITLE_LEN = 80

    def __init__(self, config):
        """initialize tanuki instance."""
        if config['DEBUG']:
            self.log = console_logger(__name__)
        else:
            self.log = console_logger(__name__, logging.INFO)
        self.config = config
        self.log.debug(self.config)

    def db_connect(self):
        """connect to default DB."""
        if request.path.startswith('/help'):
            dbfile = os.path.join(os.path.dirname(__file__),
                                  Tanuki.DEFAULT_HELP_DB)
        else:
            dbfile = os.path.join(os.path.dirname(__file__),
                                  Tanuki.DEFAULT_DB)
        self.dbfile = dbfile
        self.log.info("Connecting %s" % (dbfile))
        self.con = sqlite3.connect(dbfile)
        self.con.execute('pragma foreign_keys = on')  # !important
        self.db = self.con.cursor()

    def db_disconnect(self):
        """teardown DB."""
        nchanges = self.con.total_changes
        msg = "Disconnect %s (%s changes)" % (self.dbfile, nchanges)
        self.log.info(msg)
        self.con.close()

    def db_query(self, sql, val=''):  # TODO: ORM
        """query database."""
        self.log.debug("%s | %s" % (sql, ''.join(str(val))))
        return self.db.execute(sql, val)

    def get_status(self):
        """get and set status data, mostly counts."""
        self.status = {'entries': self.get_num_entries(),
                       'tags': len(self.get_tag_set()),
                       'notag': len(self.get_notag_entries())}

    def get_num_entries(self):
        """returns count of entries table."""
        sql = 'select count(*) from entries'
        return self.db_query(sql).fetchone()[0]

    def get_status_msg(self):
        """return status string for most routes."""
        return "%d entries %d tags " % (self.status['entries'],
                                        self.status['tags'])

    def get_tags_status_msg(self):
        """return /tags status string."""
        notag_link = '<a href="/notag">notag</a>'
        return "%d entries %d tags (%d %s) " % (self.status['entries'],
                                                self.status['tags'],
                                                self.status['notag'],
                                                notag_link)

    def render_new_form(self):
        entry = {'date': datetime.date.today().isoformat(),
                 'text': 'text',
                 'title': 'title',
                 'tags': 'tags',
                 'public': 0}
        return render_template('edit.html',
                               entry=entry,
                               title='new entry')

    def render_edit_form(self, entry_id):
        entry = self.get_entry(entry_id, True)
        referrer = request.referrer
        if not referrer:
            referrer = "/entry/%s" % entry_id
        title = "edit %s: %s" % (entry_id, entry['title'])
        return render_template('edit.html',
                               entry=entry,
                               referrer=referrer,
                               title=title,
                               status=self.status)

    def clear_tags(self, entry_id):
        """remove all tags referencing given id."""
        self.db_query("delete from tags where id=?", [entry_id])

    def store_tags(self, entry_id, tags):
        """store tags specified in edit form"""
        self.clear_tags(entry_id)
        for count, tag in enumerate(normalize_tags(tags)):
            if (count + 1) > Tanuki.MAX_TAGS_PER_ENTRY:
                return
            sql = 'insert into tags values(?,?,?)'
            date = datetime.date.today().isoformat()
            self.db_query(sql, [entry_id, tag[:Tanuki.MAX_TAG_LEN], date])

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
        """purge entry and associated tags."""
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
        """update entries dict w/tag list or comma-seperated list if
        editing.
        """
        for x in entries:
            tags = self.get_tags(x['id'])
            if editing:
                x['tags'] = ', '.join(str(x) for x in tags)
            else:
                x['tags'] = tags
        return entries

    def markdown_entries(self, entries):
        """return Markdown text from HTML entries"""
        for x in entries:
            nbytes = sys.getsizeof(x['text'])
            self.log.debug("markdown %d (%d bytes)" % (x['id'], nbytes))
            x['text'] = markdown.markdown(x['text'])
        return entries

    def pre_markdown(self, entries):
        """pre-markdown needful operations."""
        for x in entries:
            self.log.debug("pre_markdown %d" % x['id'])
            if re.match(r'^<video|<iframe|<object', x['text']):
                x['mediatype'] = 'video'
        return entries

    def get_latest_entries(self):
        """return last ten entries updated."""
        sql = 'select * from entries order by updated desc limit 10'
        return [entry2dict(x) for x in self.db_query(sql)]

    def render_index(self, page=0):
        readme = self.get_entries_tagged("readme")
        return render_template('index.html',
                               title=self.status['entries'],
                               latest=self.get_latest_entries(),
                               readme=readme,
                               tag_set=self.get_tag_set(),
                               status=self.status)

    def get_entries(self):
        """return fully hydrated entries ordered by date."""
        sql = 'select * from entries order by date desc,id desc'
        entries = [entry2dict(x) for x in self.db_query(sql)]
        self.log.debug("entries %d bytes" % (sys.getsizeof(entries)))
        return entries

    def render_list(self):
        entries = self.get_entries()  # consider removing text
        return render_template('list.html',
                               title="list (%d)" % len(entries),
                               entries=entries,
                               status=self.status)

    def get_entry(self, entry_id, editing=False):
        """returns single entry as HTML or markdown text."""
        sql = 'select * from entries where id=?'
        row = self.db_query(sql, [entry_id]).fetchone()
        if not row:
            abort(404)
        entry = [entry2dict(row)]
        entry = self.apply_tags(entry, editing)
        if not editing:
            entry = self.pre_markdown(entry)
            entry = self.markdown_entries(entry)
        return entry[0]

    def render_entry(self, entry_id):
        entry = self.get_entry(entry_id)
        return render_template('entry.html',
                               entry=entry,
                               title=entry['title'],
                               status=self.status)

    def get_tag_set(self):
        """return dict of tag names keyed on count."""
        sql = 'select count(*),name from tags group by name order by name'
        return [{'count': r[0], 'name': r[1]} for r in self.db_query(sql)]

    def render_tags(self):
        tag_set = self.get_tag_set()
        return render_template('tags.html',
                               title="tags (%d)" % len(tag_set),
                               tag_set=tag_set,
                               status=self.status)

    def msg_options(self, tag, view='list'):  # TODO: poor implementation
        opt1 = '<b>list</b>'
        opt2 = '<a href="/tagged/%s/v:gallery">gallery</a>' % (tag)
        if view == 'gallery':
            opt1 = '<a href="/tagged/%s">list</a>' % (tag)
            opt2 = '<b>gallery</b>'
        return " &mdash; " + ' | '.join([opt1, opt2])

    def get_entries_tagged(self, tag):
        """return entries matching tag name ordered by date."""
        sql = ("select * from entries,tags where tags.name=? and "
               "tags.id=entries.id order by date desc")
        return [entry2dict(x) for x in self.db_query(sql, [tag])]

    def render_tagged(self, tag, view=None):
        tagged = self.get_entries_tagged(tag)
        num = len(tagged)
        title = "#%s (%d)" % (tag, num)
        if view == 'gallery':
            return self.render_tagged_gallery(title, msg, tagged)
        return render_template('list.html',
                               title=title,
                               entries=tagged,
                               tag=tag,
                               status=self.status)

    def get_entries_img_src(self, entries):
        """update entries with <img> src attribute."""
        for x in entries:
            x['img'] = None if not x['text'] else img_src(x['text'])
            self.log.debug("%d %s" % (x['id'], x['img']))
        return entries

    def render_tagged_gallery(self, title, msg, entries):
        tagged = self.markdown_entries(entries)
        tagged = self.get_entries_img_src(tagged)
        found = set(x['img'] for x in tagged if x['img'])
        return render_template('gallery.html',
                               title=title,
                               msg=msg,
                               entries=tagged,
                               found=found)

    def get_notag_entries(self):
        """return entries having no tags."""
        sql = 'select * from entries where id not in (select id from tags)'
        return [entry2dict(x) for x in self.db_query(sql)]

    def render_notags(self):
        notag = self.get_notag_entries()
        return render_template('list.html',
                               title="notag (%d)" % len(notag),
                               entries=notag,
                               notag=True,
                               status=self.status)

    def render_search_form(self):
        return render_template('search.html', status=self.status)

    def get_entries_matching(self, terms):
        """return entries matching terms in title or text."""
        terms = '%' + terms.encode('ascii', 'ignore') + '%'
        sql = ("select * from entries where title like ? or text like ? "
               "order by id desc")
        val = [terms, terms]
        return [entry2dict(x) for x in self.db_query(sql, val)]

    def render_search_results(self, terms):
        found = self.get_entries_matching(terms)
        msg = 'found (%d) matching "%s"' % (len(found), terms)
        return render_template('list.html',
                               msg=msg,
                               entries=found,
                               status=self.status)

    def get_help_entries(self):
        """return entries from help.db."""
        sql = 'select * from entries'
        return [entry2dict(x) for x in self.db_query(sql)]

    def render_help(self):
        return render_template("help.html",
                               entries=self.get_help_entries(),
                               title="help",
                               status=self.status)


def console_logger(user_agent, level=logging.DEBUG):
    """return logger emitting to console."""
    lgr = logging.getLogger(user_agent)
    lgr.setLevel(logging.DEBUG)
    fmtr = logging.Formatter("%(name)s %(levelname)s %(funcName)s: "
                             "%(message)s")
    clog = logging.StreamHandler(sys.stdout)
    clog.setLevel(level)
    clog.setFormatter(fmtr)
    lgr.addHandler(clog)
    return lgr


def date_str(date):
    """return "Mon 1 Jan 1970" from 'YYYY-mm-dd'."""
    try:
        date = datetime.datetime.strptime(date, '%Y-%m-%d')
        return date.strftime('%a %d %b %Y')
    except:
        return 'MALFORMED'


def entry2dict(row):
    """map entries DB row to dict."""
    return {'id': row[0],
            'title': row[1],
            'text': row[2],
            'date': row[3],
            'updated': row[4],
            'public': row[5],
            'year': parse_ymd(row[3])[0],
            'month': parse_ymd(row[3])[1],
            'date_str': date_str(row[3]),
            'mediatype': 'text'}


def img_src(html):
    """return (first) <img> src attribute from HTML."""
    import lxml.html
    doc = lxml.html.document_fromstring(html)
    for src in doc.xpath("//img/@src"):
        return src


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


def utcnow():
    """return simpler ISO datetime (UTC) string."""
    return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
