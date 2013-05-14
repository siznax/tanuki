"""
tanuki class
"""
__author__ = "siznax"
__version__ = 2012

from flask import Flask,render_template,make_response,redirect,url_for,Markup,request
from werkzeug.exceptions import NotFound

import markdown
import datetime
import re
import sqlite3
import string
import sys
import urlparse

class Tanuki:

    def __init__( self, config ):
        self.config = config
        self.stream_per_page = 12
        self.DEBUG = 1
        self.editing = False
        self.mode = None
        if self.DEBUG:
            print self.config

    def connect( self ):
        dbfile = self.config['DATABASE']
        if self.DEBUG: print "+ TANUKI connecting to %s" % ( dbfile )
        self.con = sqlite3.connect( dbfile )
        self.con.execute('pragma foreign_keys = on') # !important
        self.db = self.con.cursor()

    def dbquery( self, sql, val='' ):
        if not request.host == self.config['WRITE_HOST']:
            if not sql.startswith('select'):
                raise RuntimeError
        msg = "+ TANUKI SQL: %s" % ( sql )
        if val: msg += " VAL: %s" % ( ''.join( str(val) ) )
        result = self.db.execute( sql, val )
        if self.DEBUG: print msg
        return result

    def num_entries( self ):
        sql = 'select count(*) from entries'
        return self.dbquery( sql ).fetchone()[0]

    def tag_set( self ):
        sql = 'select count(*),name from tags group by name order by name'
        return [ {'count':r[0],'name':r[1]} for r in self.dbquery( sql ) ]

    def tag_hrefs( self, tag_set, br=False ):
        hrefs = []
        for t in tag_set:
            href = "<a href=\"/tagged/%s\"># %s</a>" % ( t, t )
            hrefs.append(href)
        if br:
            return "<br />".join( hrefs )
        return " ".join( hrefs )

    def div( self, _id, _class, href=None ):
        onclick = 'onclick="window.location=\'%s\';"' % href if href else ''
        return '<div id="%s" class="%s" %s></div>' % ( _id, _class or '', onclick )

    def img( self, alt, href=None ):
        img = '<img id="%s" alt="%s" src="/static/%s.png">'\
            % ( alt, alt,  alt )
        if href:
            return '<a href="%s">%s</a>' % ( href, img )
        else:
            return img

    def new( self ):
        date = datetime.date.today().isoformat()
        n={ 'date':date,'text':'text','title':'title','tags':'tags' }
        controls = ['home','list','tags','search']
        return render_template( 'edit.html', 
                                entry=n, 
                                controls = self.controls( 0, controls ),
                                title='new entry' )

    def edit( self, entry_id ):
        self.mode = 'edit'
        if not request.host == self.config['WRITE_HOST']:
            raise NotFound()
        entry = self.entry( entry_id, False, None, True )
        referrer = request.referrer
        if not referrer:
            referrer = "/entry/%s" % entry_id
        controls = ['home','list','tags','search','new']
        return render_template( 'edit.html', 
                                entry = entry,
                                referrer = referrer,
                                title = "edit %s: %s" % ( entry_id, entry['title'] ),
                                controls = self.controls( 0, controls ),
                                body_class = self.mode)

    def clear_tags( self, entry_id ):
        self.dbquery("delete from tags where id=?", [entry_id] )

    def norm_tags( self, blob ):
        norm = []
        # lower, strip, split, unique
        for tag in set(''.join(blob.lower().split()).split(',')):
            # remove punctuation
            exclude = set(string.punctuation)
            norm.append(''.join(ch for ch in tag if ch not in exclude))
        return norm

    def store_tags( self, entry_id, tags ):
        self.clear_tags( entry_id )
        if not tags or tags == 'tags':
            return 
        for tag in self.norm_tags( tags ):
            sql = 'insert into tags values(?,?,?)'
            date = datetime.date.today().isoformat()
            self.dbquery( sql, [ entry_id, tag, date ] )

    def bad_str( self, instr ):
        try:
            type(int(instr))
            return True # disallow INT only
        except ValueError:
            return False

    def upsert( self, req ):
        self.environ = req.environ
        try:
            if self.bad_str( req.form['title'] ): raise ValueError
            if self.bad_str( req.form['entry'] ): raise ValueError
            if 'entry_id' in req.form.keys():
                sql = 'update entries set title=?, text=?, date=?, updated=? where id=?'
                val = ( req.form['title'], 
                        req.form['entry'],
                        req.form['date'],
                        self.utcnow(),
                        req.form['entry_id'] )
                self.dbquery( sql, val )
                entry_id = req.form['entry_id']
            else:
                sql = 'insert into entries values(?,?,?,?,?)'
                val = [ None,
                        req.form['title'], 
                        req.form['entry'],
                        req.form['date'],
                        None ]
                cur = self.dbquery( sql, val )
                entry_id = cur.lastrowid

            self.store_tags( entry_id, req.form['tags'] )
            self.con.commit()

            entry = self.entry( None, None, req.form['title'] )
            url = "%s/entry/%s" % ( self.environ['HTTP_ORIGIN'], entry['id'] )
            ref = req.form['referrer'] if 'referrer' in req.form else url
            return redirect( ref )
        except ValueError:
            msg = "ValueError raised, try again."
            return render_template( 'error.html', msg=msg )
        except sqlite3.IntegrityError:
            msg = "Try again, title or text not unique."
            return render_template( 'error.html', msg=msg )

    def confirm_msg( self, msg, entry ):
        deets = "ID: %d<br />\nTitle: %s<br />\nDate: %s<br />\n"\
            % ( entry['id'], entry['title'], entry['date'] )
        return "<b>%s</b><br />\n<div id=\"details\">%s</div>\n"\
            % ( msg, deets )

    def confirm( self, entry_id ):
        if not request.host == self.config['WRITE_HOST']:
            raise NotFound()
        entry = self.entry( entry_id )
        msg = self.confirm_msg( 'Really, destroy?', entry )
        return render_template( 'confirm.html', entry=entry, msg=msg )

    def delete( self, entry_id ):
        self.clear_tags( entry_id )
        self.dbquery( 'DELETE from entries WHERE id=?', [entry_id] )
        self.con.commit()

    def get_tags( self, eid ):
        t = []
        for r in self.dbquery( 'select name from tags where id=?', [eid] ):
            t.append( r[0] )
        return sorted(t)

    def apply_tags( self, entries ):
        for x in entries:
            tags = self.get_tags( x['id'] )
            x['tags'] = ', '.join(tags) if self.editing else tags
        return entries

    def utcdate( self ):
        return datetime.datetime.utcnow().strftime("%Y-%m-%d")

    def utcnow( self ):
        return datetime.datetime.utcnow().strftime("%Y-%m-%dT%H:%M:%SZ")
    
    def date_str( self, date ):
        try:
            return datetime.datetime.strptime( date ,'%Y-%m-%d').strftime('%a %d %b %Y')
        except:
            return 'MALFORMED'

    def ymd( self, date ):
        parsed = datetime.datetime.strptime( date ,'%Y-%m-%d')
        return [ parsed.strftime('%Y'), 
                 parsed.strftime('%b'), 
                 parsed.strftime('%d') ] 

    def demux( self, row ):
        # overevaluated, don't try to do much here
        ymd = self.ymd( row[3] ) 
        text = row[2]
        if request.path=='/list' or request.path=='/tags':
            text = None # unless we need it
        return  { 'id': row[0],
                  'title': row[1],
                  'text': row[2], 
                  'date': row[3],
                  'year': ymd[0],
                  'month': ymd[1],
                  'date_str': self.date_str( row[3] ),
                  'mediatype': 'text' }

    def markdown( self, entry_id, text ):
        if self.DEBUG:
            print "+ TANUKI markdown %d %d bytes"\
                % ( entry_id, sys.getsizeof( text ) )
        return markdown.markdown( text )

    def markup( self, entries ): # Warning! this can be slow
        for x in entries:
            if self.DEBUG: 
                print "+ TANUKI markup %d %d bytes"\
                    % ( x['id'], sys.getsizeof(x['text'] ) )
            x['text'] = markdown.markdown( x['text'] )
        return entries

    def controls( self, entry_id, wanted=None ):
        c = { 
            'home'  : self.img('home',  '/' ),
            'new'   : self.img('new',   '/new' ) if request.host == self.config['WRITE_HOST'] else '',
            'entry' : self.img('entry', "/entry/%d" % ( entry_id ) ) if not '/entry' in request.path else '',
            'edit'  : self.img('edit',  "/edit/%d" % ( entry_id )) if request.host == self.config['WRITE_HOST'] else '',
            'delete': self.img('delete',"/confirm/%d" % ( entry_id )) if request.host == self.config['WRITE_HOST'] else '',
            'list'  : self.img('list',  '/list' ),
            'tags'  : self.img('tags',  '/tags' ),
            'search': self.img('search','/search' )
            }
        s = "\n"
        for w in wanted:
            s += "%s\n" % ( c[w] )
        return s

    def href2img( self, href, alt ):
        img = '<img alt="%s" title="%s" src="%s">' % ( alt, alt, href )
        return '<a href="%s">%s</a>' % ( href, img )

    def preprocess( self, entries ): # before markdown
        if self.editing:
            return entries
        for x in entries:
            if self.DEBUG: 
                print "+ TANUKI preprocess %d" % ( x['id'] )
            if x['text'].startswith('http'):
                x['mediatype'] = 'img'
                text = x['text'].strip()
                lines = text.split("\n")
                first_line = lines[0].strip()
                first_word = lines[0].split()[0]
                # convert URL to <img>
                img_tag = self.href2img( first_line, x['title'] )
                x['text'] = "%s\n%s" % ( img_tag, "\n".join( lines[1:] ) )
            if re.match( r'^<video|<iframe|<object',x['text'] ):
                x['mediatype'] = 'video'
        return entries

    def postprocess( self, entries ): # AFTER markdown
        if self.editing:
            return entries
        for x in entries:
            if self.DEBUG: 
                print "+ TANUKI postprocess %d" % ( x['id'] )
            x['img'] = self.find_img( x['text'] )
        return entries

    def entry( self, entry_id, markup=False, title=None, editing=False ):
        if editing:
            self.editing = True
        if title:
            sql = 'select * from entries where title=?'
            row = self.dbquery( sql, [title] ).fetchone()
        else:
            sql = 'select * from entries where id=?'
            row = self.dbquery( sql, [entry_id] ).fetchone()
        if not row:
            return None
        entries = [self.demux( row )]
        entries = self.apply_tags( entries )
        entries = self.preprocess( entries )
        if markup:
            entries = self.markup( entries )
        self.editing = False
        return entries[0]

    def entries( self, date=None, tag=None, notag=False, terms=None, latest=None ):
        limit = False
        if date:
            sql = 'select * from entries where date=? order by id desc'
            rows = self.dbquery( sql, [date] )
        elif tag:
            sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id order by date desc'
            rows = self.dbquery( sql, [tag] )
        elif notag:
            sql = 'select * from entries where id not in (select id from tags)'
            rows = self.dbquery( sql )
        elif terms:
            terms = '%' + terms.encode('ascii','ignore')  + '%'
            sql = 'select * from entries where title like ? or text like ? order by id desc'
            rows = self.dbquery( sql, [ terms,terms ] )
        elif latest:
            sql = 'select * from entries order by updated desc limit 10'
            rows = self.dbquery( sql )
        else:
            sql = 'select * from entries order by date desc,id desc'
            rows = self.dbquery( sql )
            limit = True
        entries = [ self.demux( x ) for x in rows ]
        if self.DEBUG: 
            print "+ TANUKI entries %d bytes" % ( sys.getsizeof(entries) )
        return entries

    def slice( self, entries, page, num, noop=False ):
        total = len(entries)
        first = page * num
        last = first + num if ( first + num ) < total else total
        if first >= last:
            raise ValueError
        if noop:
            chunk = entries[first:last]
        else:
            chunk = self.apply_tags( entries[first:last] )
            chunk = self.preprocess( chunk )
            chunk = self.markup( chunk )
        return { 'num': num,
                 'total': total,
                 'start': first + 1,
                 'last': last,
                 'entries': chunk,
                 'num_pages': total / num }

    def next_prev( self, chunk, page, url='page' ):
        np = page + 1 if ( page + 1) <= chunk['num_pages'] else 0
        pp = page - 1
        n = self.div( 'next', 'btn', "/%s/%d" % ( url, np )) if np > 0 else ''
        p = self.div( 'prev', 'btn', "/%s/%d" % ( url, pp )) if pp >= 0 else ''
        return "%s%s\n" % ( p, n )

    def from_to( self, start, last ):
        if not start==last: return "%s&ndash;%s" % ( start,last )
        return start
        
    def index( self, page=0 ):
        tags = []
        entries = {}
        tag_set = self.tag_set()
        names = [ t['name'] for t in tag_set ]
        for tag in tags:
            entries[ tag ] = { 
                'count': tag_set[ names.index( tag ) ]['count'],
                'entries': self.entries( None, tag )[0:10] }
        notag = self.entries( None, None, True )
        latest = self.entries( None, None, False, None, True )
        controls = ['home','list','tags','search','new']
        return render_template( 'index.html',
                                controls = self.controls( 0, controls ),
                                tags = tags,
                                tag_set = tag_set,
                                entries = entries,
                                num_entries = self.num_entries(),
                                notag = notag,
                                latest = latest,
                                body_class = 'index' )

    def stream( self, page=0 ):
        self.mode = 'stream'
        try:
            chunk = self.slice( self.entries(), page, self.stream_per_page )
        except ValueError:
            return redirect( url_for('index') )
        controls = None
        if not page and not chunk['entries']:
            msg = "<div id=\"no_entries\">%s %s %s</div>"\
                % ( self.img( 'tanuki', None ),
                    "<b>Unbelievable. No entries yet.</b><br />",
                    "<input type=\"button\" value=\"new\" id=\"new_btn\" "\
                        "onclick=\"window.location='/new'\">" )
        else:
            controls = ['home','list','tags','search','new']
            from_to = self.from_to( chunk['start'], chunk['last'] )
            msg = "%s of %d entries" % ( from_to, chunk['total'] )
        return render_template( 'index.html',
                                controls=self.controls( 0, controls ),
                                next_prev=self.next_prev( chunk, page ),
                                entries=chunk['entries'],
                                msg=msg,
                                start=chunk['start'] )

    def find_img( self, html ):
        import lxml.html
        doc = lxml.html.document_fromstring( html )
        for src in doc.xpath("//img/@src"):
            return src

    def iframe_src( self, text ):
        src = re.search(r'src="([^"]*)"', text )
        if src:
            return src.groups()[0]
        src = re.search(r"src='([^']*)'", text )
        if src:
            return src.groups()[0]
        return None

    def iframe_stub( self, text ):
        stub = 'IFRAME STUB'
        netloc = 'netloc'
        src = self.iframe_src( text )
        if src:
            url = urlparse.urlparse( src )
            stub = '{ <a href="%s">%s</a> }' % ( src, url.netloc )
        return re.sub( r'<iframe.*iframe>', stub, text )

    def strip_tags( self, html ):
        return Markup( html ).striptags()

    # DEPRECATED: things done here should set members of each 
    # entry in postprocessing. then let the template use them.
    def grid_cells( self, entries ):
        for x in entries:
            if x['mediatype'] == 'text': 
                # strip tags and extract img src 
                html = self.markdown( x['id'], x['text'] )
                x['img'] = self.find_img( html )
                x['text'] = self.strip_tags( html )
            if x['mediatype'] == 'video':
                x['text'] = self.iframe_stub( x['text'] )
        return entries

    def result_words( self, total, from_to=None ):
        if ( from_to ):
            return "%s of %d entries" % ( from_to, total )
        else:
            return "%d entries" % ( total )

    def list( self ):
        entries = self.entries() # consider removing text
        if not entries:
            msg = "<h1>Unbelievable. No entries yet.</h1>"
        else:
            msg = self.result_words( len(entries) )
            controls = self.controls( 0, ['home','tags','search','new'] )
        return render_template( 'list.html', 
                                msg=msg, 
                                controls=controls, 
                                entries=entries )

    def singleton( self, entry_id ):
        self.mode = 'singleton'
        entry = self.entry( entry_id, True )
        if not entry:
            return redirect( url_for('index') )
        controls = ['home','list','tags','search','new','edit','delete']
        return render_template( 'entry.html', 
                                controls=self.controls( entry_id, controls ),
                                next_prev=None,
                                entry=entry,
                                title=entry['title'],
                                body_class=self.mode)

    def dated( self, date ):
        self.mode = None
        stamped = self.entries( date )
        stamped = self.apply_tags( stamped )
        stamped = self.preprocess( stamped )
        stamped = self.markup( stamped )
        msg = "%d dated %s" % ( len(stamped), self.date_str( date ) )
        controls = self.controls( 0, ['home','list','tags','search','new'] )
        return render_template( 'index.html', 
                                entries=stamped, 
                                controls = controls,
                                msg=msg )

    def tagged_views( self, tag, view ):
        if view:
            a1 = '<a href="/tagged/%s">list</a>' % ( tag )
        else:
            a1 = '<b>list</b>'
        if view == 'gallery': 
            a2 = '<b>gallery</b>'
        else:
            a2 = '<a href="/tagged/%s/gallery">gallery</a>' % ( tag )
        return ' | '.join ( [ a1, a2 ] )

    def tagged( self, tag, view=None ):
        self.mode = None
        haztag = self.entries( None, tag )
        haztag = self.apply_tags( haztag )
        haztag = self.preprocess( haztag )
        haztag = self.markup( haztag )
        haztag = self.postprocess( haztag )
        controls = ['home','list','tags','search','new']
        title = "%d tagged { %s } " % ( len(haztag), tag )
        msg = "%s %s" % ( title, self.tagged_views( tag, view ) )
        template = 'list.html'
        if view == 'gallery':
            template = 'gallery.html'
        return render_template( template,
                                msg = msg,
                                controls = self.controls( 0, controls ),
                                title = title,
                                entries = haztag ) 
        
    def tags( self ):
        self.mode = None
        entries = self.entries()
        tag_set = self.tag_set()
        notag = self.entries( None, None, True )
        if not entries:
            msg = "<h1>Unbelievable. No tags yet.</h1>"
        else:
            msg = '%d tags | %d entries | <i>%d <a href="/notag">notag</a></i>'\
                % ( len(tag_set), len(entries), len(notag) )
        controls = self.controls( 0, ['home','list','search','new'] )
        return render_template( 'tags.html', 
                                msg=msg, 
                                controls=controls, 
                                tag_set=tag_set )

    def notag( self ):
        self.mode = None
        untagged = self.entries( None, None, True )
        untagged = self.apply_tags( untagged )
        untagged = self.preprocess( untagged )
        untagged = self.markup( untagged )
        controls = ['home','list','tags','search','new']
        return render_template( 'list.html', 
                                msg = "%d not tagged" % len(untagged),
                                controls = self.controls( 0, controls), 
                                entries=untagged )
    def search( self ):
        controls = self.controls( 0, ['home','list','tags','new'] )
        return render_template('search.html', controls = controls )
        
    def matched( self, terms ):
        self.mode = None
        found = self.entries( None, None, False, terms )
        controls = ['home','list','tags','search','new']
        return render_template( 'list.html', 
                                msg = "%d matched { %s }" % ( len(found), terms ),
                                controls = self.controls( 0, controls ),
                                entries = found )

