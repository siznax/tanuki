"""
tanuki class
"""
__author__ = "siznax"
__version__ = 2012

from flask import Flask,render_template,make_response,redirect,url_for,Markup,request
import markdown
import datetime
import sqlite3
import string

class Tanuki:

    def __init__( self, config ):
        self.config = config
        self.date = datetime.date.today().isoformat()
        self.num_per_page = 10
        self.DEBUG = 1
        self.editing = False

    def connect( self ):
        dbfile = self.config['DATABASE']
        if self.DEBUG: print "+ TANUKI connecting to %s" % ( dbfile )
        self.con = sqlite3.connect( dbfile )
        self.con.execute('pragma foreign_keys = on') # !important
        self.db = self.con.cursor()

    def dbquery( self, sql, val='' ):
        msg = "+ TANUKI SQL: %s" % ( sql )
        if val:
            msg += " VAL: %s" % ( ''.join( str(val) ) )
        result = self.db.execute( sql, val )
        if self.DEBUG: print msg
        return result

    def tag_set( self ):
        sql = 'select count(*),name from tags group by name order by count(*) desc'
        tmp = [ {'count':r[0],'name':r[1]} for r in self.dbquery( sql ) ]
        self.total_tags = len( tmp )
        # print tmp
        return tmp

    def tag_hrefs( self, tag_set, br=False ):
        hrefs = []
        for t in tag_set:
            href = "<a href=\"/tagged/%s\"># %s</a>" % ( t, t )
            hrefs.append(href)
        if br:
            return "<br />".join( hrefs )
        return " ".join( hrefs )

    def img( self, alt, href=None ):
        img = '<img id="%s" alt="%s" align="top" src="/static/%s.png">'\
            % ( alt, alt, alt )
        if href:
            return '<a href="%s">%s</a>' % ( href, img )
        else:
            return img

    def new( self ):
        return render_template( 'edit.html', 
                                entry={ 'date': self.date,
                                        'text': 'text',
                                        'title': 'title',
                                        'tags': 'tags' } )

    def edit( self, entry_id ):
        entry = self.entry( entry_id, False, None, True )
        return render_template( 'edit.html', entry=entry )

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
            self.dbquery( sql, [ entry_id, tag, self.date ] )

    def upsert( self, req ):
        self.environ = req.environ
        try:
            if 'entry_id' in req.form.keys():
                entry_id = req.form['entry_id']
                sql = 'update entries set title=?, text=?, date=? where id=?'
                val = ( req.form['title'], 
                        req.form['entry'],
                        req.form['date'],
                        entry_id )
                self.dbquery( sql, val )
            else:
                sql = 'insert into entries values(?,?,?,?)'
                val = [ None,
                        req.form['title'], 
                        req.form['entry'],
                        req.form['date'] ]
                cur = self.dbquery( sql, val )
                entry_id = cur.lastrowid

            self.store_tags( entry_id, req.form['tags'] )

            self.con.commit()
            entry = self.entry( None, None, req.form['title'] )
            return redirect( req.form['referrer'] )
        except sqlite3.IntegrityError:
            msg = "Try again, title or text not unique."
            return render_template( 'error.html', msg=msg )

    def confirm_msg( self, msg, entry ):
        deets = "ID: %d<br />\n"\
            "Title: %s<br />\n"\
            "Date: %s<br />\n"\
            % ( entry['id'], entry['title'], entry['date'] )
        return "<b>%s</b><br />\n"\
            "<div id=\"details\">%s</div>\n"\
            % ( msg, deets )

    def confirm( self, entry_id ):
        entry = self.entry( entry_id )
        msg = self.confirm_msg( 'Really, destroy?', entry )
        return render_template( 'confirm.html', 
                                entry=entry,
                                msg=msg )

    def delete( self, entry_id ):
        self.clear_tags( entry_id )
        sql = 'DELETE from entries WHERE id=?'
        self.dbquery( sql, [entry_id] )
        self.con.commit()

    def get_tags( self, entry_id ):
        tags = []
        sql = 'select name from tags where id=?'
        for row in self.dbquery( sql, [entry_id] ):
            tags.append( row[0] )
        return sorted(tags)

    def apply_tags( self, entries ):
        for x in entries:
            tags = self.get_tags( x['id'] )
            x['tags'] = ', '.join(tags) if self.editing else tags
        return entries

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
        return  { 'id': row[0],
                  'title': row[1],
                  'text': row[2], 
                  'date': row[3],
                  'year': ymd[0],
                  'month': ymd[1],
                  'date_str': self.date_str( row[3] ),
                  'mediatype': 'text' }

    def markup( self, entries ): # Warning! this can be slow
        for x in entries:
            if self.DEBUG: print "+ TANUKI markup %d %d"\
                    % ( x['id'], len(x['text'] ) )
            x['text'] = markdown.markdown( x['text'] )
        return entries

    def controls( self, entry_id, wanted=None ):
        c = { 'home': self.img( 'home', '/' )\
                  if not request.path=='/' else '',
              'new': self.img( 'new', '/new' ),
              'entry': self.img( 'entry', "/entry/%d" % ( entry_id ))\
                  if not '/entry' in request.path else '',
              'edit': self.img( 'edit', "/edit/%d" % ( entry_id )),
              'list': self.img( 'list', '/list' ),
              'cloud': self.img( 'cloud', '/cloud' ),
              'search': self.img( 'search', '/search' ),
              'grid': self.img( 'grid', '/grid' ) }
        s = ''
        for w in wanted:
            s += "%s" % ( c[w] )
        return s

    def inline( self, entry, alt, src, caption, media=False ):
        caption = markdown.markdown( caption )
        if '/entry' in request.path: entry_img = ''
        if not media:
            media = "<a href=\"/entry/%d\">"\
                "<img alt=\"%s\" title=\"%s\" src=\"%s\"></a>\n"\
                % ( entry['id'], alt, alt, src )
        return "<div id=\"figure\">\n"\
            "<span id=\"controls\">%s</span>\n"\
            "<span id=\"tags\">%s</span>\n"\
            "<figure>\n%s"\
            "<figcaption>%s</figcaption>\n"\
            "</figure>\n</div>\n"\
            % ( self.controls( entry['id'], [ 'home', 'entry', 'edit' ] ),
                self.tag_hrefs( entry['tags'], True),
                media, caption )

    def preprocess( self, entries ):
        # do this before markdown
        if self.editing:
            return entries
        for x in entries:
            if ( x['text'].startswith('http') or 
                 x['text'].startswith('<iframe') ):
                if self.DEBUG: print "+ TANUKI preprocess %d" % ( x['id'] )
                text = x['text'].strip()
                lines = text.split("\n")
                first_line = lines[0].strip()
                first_word = lines[0].split()[0]
                cap = "\n".join( lines[1:])
                if text.startswith('http'):
                    x['mediatype'] = 'img'
                    alt = x['title']
                    src = first_word
                    text = self.inline( x, alt, src, cap )
                if text.startswith('<iframe'):
                    x['mediatype'] = 'video'
                    text = self.inline( x, None, None, cap, first_line )
                x['text'] = text
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

    def entries( self, date=None, tag=None, notag=False, terms=None ):
        limit = False
        if date:
            sql = 'select * from entries where date=? order by id desc'
            rows = self.dbquery( sql, [date] )
        elif tag:
            sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id order by date desc'
            rows = self.dbquery( sql, [tag] )
        elif notag:
            sql = 'select * from entries where id not in (select id from tags) order by id desc'
            rows = self.dbquery( sql )
        elif terms:
            terms = '%' + terms  + '%'
            sql = 'select * from entries where (title like ? or text like ?)'
            rows = self.dbquery( sql, [ terms, terms ] )
        else:
            sql = 'select * from entries order by date desc,id desc'
            rows = self.dbquery( sql )
            limit = True
        entries = [ self.demux( x ) for x in rows ]
        return entries

    def slice( self, entries, page ):
        total = len(entries)
        num = self.num_per_page
        first = page * num
        last = first + num if ( first + num ) < total else total
        if first >= last:
            raise ValueError
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
        n_p = page + 1 if ( page + 1) <= chunk['num_pages'] else 0
        p_p = page - 1
        n_i = self.img( 'next', "/%s/%d" % ( url, n_p )) if n_p > 0 else ''
        p_i = self.img( 'prev', "/%s/%d" % ( url, p_p)) if p_p >= 0 else ''
        return "<div id=\"next_prev\">\n%s%s\n</div>\n" % ( p_i, n_i ) 

    def stream( self, page=0 ):
        try:
            chunk = self.slice( self.entries(), page )
        except ValueError:
            return redirect( url_for('index') )
        if not page and not chunk['entries']:
            msg = "<div id=\"no_entries\">%s %s %s</div>"\
                % ( self.img( 'tanuki', None ),
                    "<b>Unbelievable. No entries yet.</b><br />",
                    "<input type=\"button\" value=\"new\" id=\"new_btn\" "\
                        "onclick=\"window.location='/new'\">" )
        else:
            msg = "%s %s %d to %d of %d entries %s %s %s %s %s %s"\
                % ( self.img( 'tanuki', None ),
                    self.next_prev( chunk, page ),
                    chunk['start'],
                    chunk['last'],
                    chunk['total'],
                    self.img( 'home', '/' ) if page else '',
                    self.img( 'grid', '/grid' ),
                    self.img( 'list', '/list' ),
                    self.img( 'cloud', '/cloud' ),
                    self.img( 'search', '/search' ), 
                    self.img( 'new', '/new' ))
        return render_template( 'index.html',
                                entries=chunk['entries'],
                                msg=msg,
                                start=chunk['start'] )

    def grid_cells( self, entries ):
        max_cell_len = 255
        for x in entries:
            t = Markup( x['text'] ).striptags()
            if len( t ) > max_cell_len:
                t = t[:max_cell_len] + '...'
            x['text'] = t
        return entries

    def grid( self, page=0 ):
        chunk = self.slice( self.entries(), page )
        chunk['entries'] = self.grid_cells( chunk['entries'] )
        msg = "%s %s %d to %d of %d entries %s %s %s %s"\
            % ( self.img( 'tanuki', None ),
                self.next_prev( chunk, page, 'grid' ),
                chunk['start'],
                chunk['last'], 
                chunk['total'], 
                self.img( 'home', '/' ),
                self.img( 'list', '/list' ),
                self.img( 'cloud', '/cloud' ),
                self.img( 'search', '/search' ))
        return render_template( 'grid.html',
                                entries=chunk['entries'],
                                msg=msg,
                                start=chunk['start'] )

    def list( self ):
        entries = self.entries() # consider removing text
        if not entries:
            msg = "<h1>Unbelievable. No entries yet.</h1>"
        else:
            msg = "%d entries %s %s %s %s"\
                % ( len(entries),
                    self.img( 'home', '/' ),
                    self.img( 'grid', '/grid' ),
                    self.img( 'cloud', '/cloud' ),
                    self.img( 'search', '/search' ))
        return render_template( 'index.html',
                                entries=entries,
                                msg=msg )

    def singleton( self, entry_id ):
        entry = self.entry( entry_id, True )
        if not entry:
            return redirect( url_for('index') )
        return render_template( 'index.html', entries=[ entry ] )

    def dated( self, date ):
        entries = self.entries( date )
        entries = self.apply_tags( entries )
        entries = self.markup( entries )
        date_str = self.date_str( date )
        msg = "%d dated %s %s %s %s %s"\
            % ( len(entries), 
                date_str,
                self.img( 'home', '/' ),
                self.img( 'list', '/list' ),
                self.img( 'cloud', '/cloud' ),
                self.img( 'search', '/search' ))
        return render_template( 'index.html', entries=entries, msg=msg )

    def tagged( self, tag ):
        haztag = self.entries( None, tag )
        haztag = self.apply_tags( haztag )
        haztag = self.preprocess( haztag )
        haztag = self.markup( haztag )
        msg = "%d tagged %s %s %s %s %s"\
            % ( len(haztag), 
                tag,
                self.img( 'home', '/' ),
                self.img( 'list', '/list' ),
                self.img( 'cloud', '/cloud' ),
                self.img( 'search', '/search' ))
        return render_template( 'index.html', 
                                entries=haztag,
                                msg=msg )
        
    def cloud( self ):
        entries = self.entries()
        tag_set = self.tag_set()
        notag = self.entries( None, None, True )
        if not entries:
            msg = "<h1>Unbelievable. No tags yet.</h1>"
        else:
            msg = "%d entries %d tags %s %s %s %s <i>%d not tagged %s</i>"\
                % ( len(entries),
                    len(tag_set),
                    self.img( 'home', '/' ),
                    self.img( 'grid', '/grid' ),
                    self.img( 'list', '/list' ),
                    self.img( 'search', '/search' ),
                    len(notag),
                    self.img( 'notag', '/notag' ))
        return render_template( 'index.html', tag_set=tag_set, msg=msg )

    def notag( self ):
        untagged = self.entries( None, None, True )
        untagged = self.apply_tags( untagged )
        untagged = self.preprocess( untagged )
        untagged = self.markup( untagged )
        msg = "%d not tagged %s %s" % ( len(untagged), 
                                        self.img( 'home', '/' ),
                                        self.img( 'cloud', '/cloud' ) )
        return render_template( 'index.html', entries=untagged, msg=msg )
        
    def matched( self, terms ):
        found = self.entries( None, None, False, terms )
        found = self.apply_tags( found )
        found = self.preprocess( found )
        found = self.markup( found )
        msg = "%d matched { %s } %s %s %s"\
            % ( len(found), 
                terms,
                self.img( 'search', '/search' ),
                self.img( 'home', '/' ),
                self.img( 'cloud', '/cloud' ))
        return render_template( 'index.html', entries=found, msg=msg )
