"""
tanuki class
"""
__author__ = "siznax"
__version__ = 2012

from flask import Flask,render_template,make_response,redirect,url_for
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

    def img( self, alt, href ):
        img = '<img id="%s" alt="%s" align="top" src="/static/%s.png">'\
            % ( alt, alt, alt )
        return '<a href="%s">%s</a>' % ( href, img )

    def new( self ):
        return render_template( 'edit.html', 
                                entry={ 'date': self.date,
                                        'text': 'text',
                                        'title': 'title',
                                        'tags': 'tags' } )

    def site_url( self, path):
        return "%s%s" % ( self.environ['HTTP_ORIGIN'], path )

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
            goto = self.site_url( "/entry/%s" % ( entry['id']) )
            return redirect( goto )
        except sqlite3.IntegrityError:
            msg = "Try again, title or text not unique."
            return render_template( 'error.html', msg=msg )

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
        return tags

    def apply_tags( self, entries, editing=False ):
        tagged = []
        for entry in entries:
            tags = self.get_tags( entry['id'] )
            entry['tags'] = ', '.join(tags) if editing else tags
            tagged.append( entry )
        return tagged

    def date_str( self, date ):
        try:
            return datetime.datetime.strptime( date ,'%Y-%m-%d').strftime('%a %d %b %Y')
        except:
            return 'MALFORMED'

    def demux( self, row ):
        return  { 'id': row[0],
                  'title': row[1],
                  'text': row[2].strip(),
                  'date': row[3],
                  'date_str': self.date_str( row[3] ) }

    def markup( self, entries ): # Warning! this can be slow
        for x in entries:
            if self.DEBUG: print "+ TANUKI markup %d" % ( len(x['text'] ) )
            x['text'] = markdown.markdown( x['text'] )
        return entries

    def entry( self, entry_id, md=False, title=None, editing=False ):
        if title:
            sql = 'select * from entries where title=?'
            row = self.dbquery( sql, [title] ).fetchone()
        else:
            sql = 'select * from entries where id=?'
            row = self.dbquery( sql, [entry_id] ).fetchone()
        if not row:
            return None
        return self.markup( self.apply_tags( [self.demux( row )], editing ) )[0]

    def entries( self, date=None, tag=None, notag=False, terms=None ):
        limit = False
        if date:
            sql = 'select * from entries where date=? order by id desc'
            rows = self.dbquery( sql, [date] )
        elif tag:
            sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id order by id desc'
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
        if first > last:
            raise ValueError
        chunk = self.markup( self.apply_tags( entries[first:last] ) )
        return { 'num': num,
                 'total': total,
                 'start': first + 1,
                 'last': last,
                 'entries': chunk,
                 'num_pages': total / num }

    def next_prev( self, chunk, page ):
        n_p = page + 1 if ( page + 1) <= chunk['num_pages'] else 0
        p_p = page - 1
        n_i = self.img( 'next', "/page/%d" % ( n_p )) if n_p > 0 else ''
        p_i = self.img( 'prev', "/page/%d" % ( p_p)) if p_p >= 0 else ''
        return "<div id=\"next_prev\">\n%s%s\n</div>\n" % ( p_i, n_i ) 

    def stream( self, page=0 ):
        try:
            chunk = self.slice( self.entries(), page )
        except ValueError:
            return redirect( url_for('index') )
        if not chunk:
            msg = "<h1>Unbelievable. No entries yet.</h1>"
        else:
            msg = "%s %d to %d of %d entries %s %s %s %s"\
                % ( self.next_prev( chunk, page ),
                    chunk['start'],
                    chunk['last'], 
                    chunk['total'], 
                    self.img( 'home', '/' ) if page else '',
                    self.img( 'list', '/list' ),
                    self.img( 'cloud', '/cloud' ),
                    self.img( 'search', '/search' ))
        return render_template( 'index.html',
                                entries=chunk['entries'],
                                msg=msg,
                                start=chunk['start'] )

    def list( self ):
        entries = self.entries() # consider removing text
        if not entries:
            msg = "<h1>Unbelievable. No entries yet.</h1>"
        else:
            msg = "%d entries %s %s %s"\
                % ( len(entries),
                    self.img( 'home', '/' ),
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
        entries = self.markup( self.apply_tags( self.entries( date ) ) )
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
        entries = self.markup( self.apply_tags( self.entries( None, tag ) ) )
        msg = "%d tagged %s %s %s %s %s"\
            % ( len(entries), 
                tag,
                self.img( 'home', '/' ),
                self.img( 'list', '/list' ),
                self.img( 'cloud', '/cloud' ),
                self.img( 'search', '/search' ))
        return render_template( 'index.html', entries=entries, msg=msg )
        
    def cloud( self ):
        entries = self.entries()
        tag_set = self.tag_set()
        notag = self.entries( None, None, True )
        if not entries:
            msg = "<h1>Unbelievable. No tags yet.</h1>"
        else:
            msg = "%d entries %d tags %s %s <i>%d not tagged %s</i>"\
                % ( len(entries),
                    len(tag_set),
                    self.img( 'home', '/' ),
                    self.img( 'search', '/search' ),
                    len(notag),
                    self.img( 'notag', '/notag' ))
        return render_template( 'index.html', tag_set=tag_set, msg=msg )

    def notag( self ):
        entries = self.markup( self.apply_tags( self.entries( None, None, True ) ) )
        msg = "%d not tagged %s %s" % ( len(entries), 
                                        self.img( 'home', '/' ),
                                        self.img( 'cloud', '/cloud' ) )
        return render_template( 'index.html', entries=entries, msg=msg )
        
    def matched( self, terms ):
        found = self.markup( self.apply_tags( self.entries( None, None, False, terms ) ) )
        msg = "%d matched { %s } %s %s %s"\
            % ( len(found), 
                terms,
                self.img( 'search', '/search' ),
                self.img( 'home', '/' ),
                self.img( 'cloud', '/cloud' ))
        return render_template( 'index.html', entries=found, msg=msg )
