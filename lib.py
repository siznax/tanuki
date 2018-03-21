from __future__ import division

import datetime
import frag2text
import logging
import lxml.html
import markdown
import os
import sqlite3
import string
import sys

from flask import render_template, request, redirect, abort

__author__ = "siznax"
__date__ = "Feb 2015"


class Tanuki:

    DEFAULT_DB = "tanuki.db"
    DEFAULT_HELP_DB = "help.db"
    MAX_ENTRY_LEN = 131072
    MAX_TAGS_PER_ENTRY = 5
    MAX_TAG_LEN = 128
    MAX_TITLE_LEN = 1024

    def __init__(self, config):
        """initialize tanuki instance."""
        if config['DEBUG']:
            self.log = console_logger(__name__)
        else:
            self.log = console_logger(__name__, logging.INFO)
        self.config = config
        self.log.debug(self.config)

    def apply_tags(self, entries, editing=False):
        """update entries dict w/tag list or comma-seperated list if
        editing.
        """
        for x in entries:
            tags = self.get_tags(x['id'])
            if editing:
                x['tags'] = ', '.join(filter(bool, (ascii(x) for x in tags)))
            else:
                x['tags'] = tags
        return entries

    def clear_tags(self, entry_id):
        """remove all tags referencing given id."""
        self.db_query("delete from tags where id=?", [entry_id])

    def db_connect(self):
        """connect to default DB."""
        if self.config.get('DATABASE'):
            if not os.path.exists(self.config['DATABASE']):
                raise ValueError("DATABASE not found: " +
                                 self.config.get('DATABASE'))
            dbfile = self.config.get('DATABASE')
        else:
            dbfile = os.path.join(os.path.dirname(__file__),
                                  Tanuki.DEFAULT_DB)
        if request.path.startswith('/help'):
            dbfile = os.path.join(os.path.dirname(__file__),
                                  Tanuki.DEFAULT_HELP_DB)
        self.log.info("Connecting %s" % (dbfile))
        self.con = sqlite3.connect(dbfile)
        self.con.execute('pragma foreign_keys = on')  # !important
        self.db = self.con.cursor()
        self.dbfile = dbfile

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

    def delete_entry(self, entry_id):
        """purge entry and associated tags."""
        self.clear_tags(entry_id)
        self.db_query('DELETE from entries WHERE id=?', [entry_id])
        self.con.commit()

    def get_entries(self):
        """return fully hydrated entries ordered by date created."""
        sql = 'select * from entries order by date desc,id desc'
        entries = [entry2dict(x) for x in self.db_query(sql)]
        self.log.debug("entries %d bytes" % (sys.getsizeof(entries)))
        return entries

    def get_entries_by_updated(self):
        """return fully hydrated entries ordered by date updated."""
        sql = 'select * from entries order by updated desc, date desc'
        entries = [entry2dict(x, 'updated') for x in self.db_query(sql)]
        self.log.debug("entries %d bytes" % (sys.getsizeof(entries)))
        return entries

    def get_entries_img_src(self, entries):
        """update entries with <img> src attribute."""
        for x in entries:
            x['img'] = None if not x['text'] else img_src(x['text'])
            self.log.debug("%d %s" % (x['id'], x['img']))
        return entries

    def get_entries_matching(self, terms):
        """return entries matching terms in title or text."""
        terms = '%' + terms.encode('ascii', 'ignore') + '%'
        sql = ("select * from entries where title like ? or text like ? "
               "order by updated desc")
        val = [terms, terms]
        return [entry2dict(x) for x in self.db_query(sql, val)]

    def get_entries_tagged(self, tag):
        """return entries matching tag name ordered by date."""
        sql = ("select * from entries,tags where tags.name=? and "
               "tags.id=entries.id order by updated desc")
        return [entry2dict(x, 'updated') for x in self.db_query(sql, [tag])]

    def get_entry(self, entry_id, editing=False):
        """returns single entry as HTML or markdown text."""
        sql = 'select * from entries where id=?'
        row = self.db_query(sql, [entry_id]).fetchone()
        if not row:
            abort(404)
        entry = [entry2dict(row)]
        entry = self.apply_tags(entry, editing)
        if not editing:
            entry = self.markdown_entries(entry)
        return entry[0]

    def get_help_entries(self):
        """return entries from help.db."""
        sql = 'select * from entries'
        return [entry2dict(x) for x in self.db_query(sql)]

    def get_latest_entries(self):
        """return last ten entries updated."""
        sql = 'select * from entries order by updated desc limit 10'
        return [entry2dict(x) for x in self.db_query(sql)]

    def get_notag_entries(self):
        """return entries having no tags."""
        sql = 'select * from entries where id not in (select id from tags)'
        return [entry2dict(x) for x in self.db_query(sql)]

    def get_num_entries(self):
        """returns count of entries table."""
        sql = 'select count(*) from entries'
        return self.db_query(sql).fetchone()[0]

    def get_status(self):
        """get and set status data, mostly counts."""
        self.status = {'entries': self.get_num_entries(),
                       'tags': len(self.get_tag_set()),
                       'notag': len(self.get_notag_entries())}

    def get_status_msg(self):
        """return status string for most routes."""
        return "%d entries %d tags " % (self.status['entries'],
                                        self.status['tags'])

    def get_tag_set(self):
        """return dict of tag names keyed on count."""
        sql = 'select count(*),name from tags group by name order by name'
        return [{'count': r[0], 'name': r[1]} for r in self.db_query(sql)]

    def get_tags(self, eid):
        """return sorted list of tag names."""
        t = []
        for r in self.db_query('select name from tags where id=?', [eid]):
            t.append(r[0])
        return sorted(t)

    def get_tags_status_msg(self):
        """return /tags status string."""
        notag_link = '<a href="/notag">notag</a>'
        return "%d entries %d tags (%d %s) " % (self.status['entries'],
                                                self.status['tags'],
                                                self.status['notag'],
                                                notag_link)

    def insert_entry(self, req):
        """executes DB INSERT, returns entry id."""
        sql = "insert into entries values(?,?,?,?,?,?)"
        val = [None,
               req.form['title'][:Tanuki.MAX_TITLE_LEN],
               req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
               req.form['date'], utcnow(), 0]
        cur = self.db_query(sql, val)
        return cur.lastrowid

    def markdown_entries(self, entries):
        """return Markdown text from HTML entries"""
        for x in entries:
            nbytes = sys.getsizeof(x['text'])
            self.log.debug("markdown %d (%d bytes)" % (x['id'], nbytes))
            x['text'] = markdown.markdown(x['text'])
        return entries

    def msg_options(self, tag, view='list'):  # TODO: poor implementation
        opt1 = '<b>list</b>'
        opt2 = '<a href="/tagged/%s/v:gallery">gallery</a>' % (tag)
        if view == 'gallery':
            opt1 = '<a href="/tagged/%s">list</a>' % (tag)
            opt2 = '<b>gallery</b>'
        return " &mdash; " + ' | '.join([opt1, opt2])

    def render_capture_form(self):
        return render_template('capture.html',
                               title='capture',
                               status=self.status)

    def render_delete_form(self, entry_id):
        entry = self.get_entry(entry_id)
        if entry['public'] > 1:
            return render_template('error.html', msg="Entry locked.")
        return render_template('delete.html', entry=entry)

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

    def render_edit_capture_form(self, endpoint, stype, selector):
        text = ("<!-- frag2text %s\n" % frag2text.__version__ +
                "endpoint: %s\nstype: %s\nselector: %s\n"
                % (endpoint, stype, selector) +
                "-->\n\n")
        try:
            text += frag2text.frag2text(
                endpoint, stype, selector).decode('utf8')
        except Exception as err:
            text += "Caught exception: %s" % err
        entry = {'date': datetime.date.today().isoformat(),
                 'text': text,
                 'title': None,
                 'tags': None,
                 'public': 0}
        return render_template('edit.html',
                               entry=entry,
                               status=self.status)

    def render_entry(self, entry_id):
        entry = self.get_entry(entry_id)
        return render_template('entry.html',
                               entry=entry,
                               title=entry['title'],
                               status=self.status)

    def render_help(self):
        return render_template("help.html",
                               entries=self.get_help_entries(),
                               title="help",
                               status=self.status)

    def render_index(self, page=0):
        readme = self.get_entries_tagged("readme")
        todo = self.get_entries_tagged("todo")
        pinned = self.get_entries_tagged("pinned")
        return render_template('index.html',
                               title="home (%d)" % self.status['entries'],
                               latest=self.get_latest_entries(),
                               readme=readme,
                               todo=todo,
                               pinned=pinned,
                               tag_set=self.get_tag_set(),
                               status=self.status)

    def render_list(self):
        """show entries by date created."""
        entries = self.get_entries()
        entries = mark_media(entries)
        return render_template('list.html',
                               title="list (%d) by created" % len(entries),
                               entries=entries,
                               sortby='created',
                               status=self.status)

    def render_list_by_updated(self):
        """show entries by date updated."""
        entries = self.get_entries_by_updated()
        entries = mark_media(entries)
        return render_template('list.html',
                               title="(%d) by updated" % len(entries),
                               entries=entries,
                               sortby='updated',
                               status=self.status)

    def render_list_media(self, mediatype):
        """show entries selected by mediatype"""
        entries = self.get_entries()
        entries = [x for x in mark_media(entries) if mediatype in x['media']]
        if not entries:
            abort(404)
        return render_template('list.html',
                               title="(%d) %s" % (len(entries), mediatype),
                               entries=entries,
                               mediatype=mediatype,
                               status=self.status)

    def render_media_count(self):
        """show media counts"""
        entries = self.get_entries()
        entries = mark_media(entries, links=False)
        return render_template('media.html',
                               title="(%d) media entries" % len(entries),
                               entries=entries,
                               media=media_count(entries),
                               status=self.status)

    def render_new_form(self):
        entry = {'date': datetime.date.today().isoformat(),
                 'text': None,
                 'title': None,
                 'tags': None,
                 'public': 0}
        return render_template('edit.html',
                               entry=entry,
                               title='new',
                               status=self.status)

    def render_notags(self):
        notag = self.get_notag_entries()
        return render_template('list.html',
                               title="notag (%d)" % len(notag),
                               entries=notag,
                               notag=True,
                               status=self.status)

    def render_tagged(self, tag, view=None):
        tagged = self.get_entries_tagged(tag)
        tagged = mark_media(tagged)
        num = len(tagged)
        title = "#%s (%d)" % (tag, num)
        if view == 'gallery':
            return self.render_tagged_gallery(title, tagged)
        return render_template('list.html',
                               title=title,
                               entries=tagged,
                               tag=tag,
                               status=self.status)

    def render_tagged_gallery(self, tag):
        tagged = self.get_entries_tagged(tag)
        tagged = self.markdown_entries(tagged)
        tagged = self.get_entries_img_src(tagged)
        images = set(x['img'] for x in tagged if x['img'])
        return render_template('gallery.html',
                               title="#%s gallery" % tag,
                               entries=tagged,
                               tag=tag,
                               images=images,
                               status=self.status)

    def render_tags(self):
        tag_set = binned_tags(self.get_tag_set())
        return render_template('tags.html',
                               title="tags (%d)" % len(tag_set),
                               tag_set=tag_set,
                               status=self.status)

    def render_search_form(self):
        return render_template('search.html',
                               title='search',
                               status=self.status,
                               tag_set=self.get_tag_set())

    def render_search_results(self, terms):
        found = self.get_entries_matching(terms)
        found = mark_media(found)
        return render_template('list.html',
                               terms=terms,
                               entries=found,
                               status=self.status)

    def store_tags(self, entry_id, tags):
        """store tags specified in edit form"""
        self.clear_tags(entry_id)
        for count, tag in enumerate(normalize_tags(tags)):
            if tag.strip():
                if (count + 1) > Tanuki.MAX_TAGS_PER_ENTRY:
                    return
                sql = 'insert into tags values(?,?,?)'
                date = datetime.date.today().isoformat()
                self.db_query(sql, [entry_id, tag[:Tanuki.MAX_TAG_LEN], date])

    def update_entry(self, req):
        """executes DB UPDATE, returns entry id."""
        sql = ("update entries set title=?,text=?,date=?,"
               "updated=?,public=? where id=?")
        val = (req.form['title'][:Tanuki.MAX_TITLE_LEN],
               req.form['entry'][:Tanuki.MAX_ENTRY_LEN],
               req.form['date'], utcnow(), 0, req.form['entry_id'])
        self.db_query(sql, val)
        return req.form['entry_id']

    def upsert(self, req):
        """update existing or insert new entry in DB."""
        try:
            if Tanuki.valid_edit_form(req):
                entry_id = self.update_entry(req)
            else:
                entry_id = self.insert_entry(req)
            self.store_tags(entry_id, req.form['tags'])
            self.con.commit()
            return redirect("/entry/%s" % (entry_id))
        except ValueError:
            return render_template('error.html',
                                   msg="ValueError raised, try again.")
        except sqlite3.IntegrityError:
            return render_template('error.html',
                                   msg="Title or text not unique, try again.")

    @staticmethod
    def valid_edit_form(req):
        """returns True if edit form validates."""
        datetime.datetime.strptime(req.form['date'], '%Y-%m-%d')
        if 'locked' in req.form:
            raise ValueError
        if str_is_int(req.form['title']):
            raise ValueError
        if str_is_int(req.form['entry']):
            raise ValueError
        if 'entry_id' in req.form.keys():
            return True
        return False


def ascii(s):
    """return just the ascii portion of a string"""
    return ''.join([c for c in s if ord(c) < 128])


def binned_tags(tag_set):
    if not tag_set:
        return []
    max_count = max([x['count'] for x in tag_set])
    t_min = 0
    f_max = 3
    for tag in tag_set:
        if tag['count'] > t_min:
            em = (f_max * (tag['count'] - t_min)) / (max_count - t_min)
            tag['em'] = round(em + 1, 2)
        else:
            tag['em'] = 1
    return tag_set


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
        return date


def entry2dict(row, sort='date'):
    """map entries DB row to dict."""
    _dict = {'id':        row[0],
             'title':     row[1],
             'text':      row[2],
             'date':      row[3],
             'date_str':  date_str(row[3]),
             'updated':   row[4],
             'public':    row[5]}
    date = row[3]
    if sort == 'updated':
        date = row[4]
    _dict['year'] = parse_ymd(date)[0]
    _dict['month'] = parse_ymd(date)[1]
    _dict['day'] = parse_ymd(date)[2]
    return _dict


def img_src(html):
    """return (first) <img> src attribute from HTML."""
    doc = lxml.html.document_fromstring(html)
    for src in doc.xpath("//img/@src"):
        return src


def link_media(media):
    return ['<a href="/media/%s">%s</a>' % (m, m) for m in media]


def mark_media(entries, links=True):
    for x in entries:
        mediatypes = ['<audio', '<iframe', '<img', '<video',
                      '.flv', '.mov', '.mp3', '.mp4', '.ogg']
        media = [rmpunc(m) for m in mediatypes if m in x['text']]
        if links:
            media = link_media(media)
        x['media'] = ', '.join(media)
    return entries


def media_count(entries):
    """expects entries with simple (not linked) media values"""
    from collections import Counter, OrderedDict
    media = []
    for item in entries:
        media.extend(item['media'].split(', '))
    return OrderedDict(sorted(Counter(media).items(),
                              key=lambda t: t[1],
                              reverse=True))


def normalize_tags(blob):
    norm = []
    # lower, strip, split, unique
    for tag in set(''.join(blob.lower().split()).split(',')):
        norm.append(ascii(rmpunc(tag)))
    return norm


def parse_ymd(date):
    """return [y, m, d] from 'YYYY-mm-dd'"""
    try:
        parsed = datetime.datetime.strptime(date[:10], '%Y-%m-%d')
        return [parsed.strftime('%Y'),
                parsed.strftime('%b'),
                parsed.strftime('%d')]
    except:
        return [None, None, None]


def rmpunc(_str):
    return ''.join(c for c in _str if c not in set(string.punctuation))


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
