"""
tanuki class
"""
__author__ = "siznax"
__version__ = 2012

import sqlite3
from markdown import markdown
import datetime
from flask import Flask,render_template,make_response,redirect,url_for

class Tanuki:

    def __init__( self, config ):
        self.config = config
        self.date = datetime.date.today().isoformat()
        self.mode = None

    def connect( self ):
        self.con = sqlite3.connect( self.config['DATABASE'] )
        self.con.execute('pragma foreign_keys = on') # !important
        self.db = self.con.cursor()

    def tag_set( self ):
        sql = 'select count(*),name from tags group by name order by count(*) desc'
        tmp = [ {'count':r[0],'name':r[1]} for r in self.db.execute( sql ) ]
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
        self.db.execute("delete from tags where id=?", [entry_id] )

    def norm_tags( self, blob ):
        norm = []
        # lower, strip, split, unique
        for tag in set(''.join(blob.lower().split()).split(',')):
            # remove punctuation
            import string
            exclude = set(string.punctuation)
            norm.append(''.join(ch for ch in tag if ch not in exclude))
        return norm

    def store_tags( self, entry_id, tags ):
        self.clear_tags( entry_id )
        if not tags or tags == 'tags':
            return 
        for tag in self.norm_tags( tags ):
            sql = 'insert into tags values(?,?,?)'
            self.db.execute( sql, [ entry_id, tag, self.date ] )

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
                self.db.execute( sql, val )
            else:
                sql = 'insert into entries values(?,?,?,?)'
                val = [ None,
                        req.form['title'], 
                        req.form['entry'],
                        req.form['date'] ]
                cur = self.db.execute( sql, val )
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
        self.db.execute( sql, [entry_id] )
        self.con.commit()

    def get_tags( self, entry_id ):
        tags = []
        sql = 'select name from tags where id=?'
        for row in self.db.execute( sql, [entry_id] ):
            tags.append( row[0] )
        return tags

    def apply_tags( self, entries):
        tagged = []
        for entry in entries:
            tags = self.get_tags( entry['id'] )
            entry['tags'] = ', '.join(tags) if self.mode=='edit' else tags
            tagged.append( entry )
        return tagged

    def date_str( self, date ):
        try:
            return datetime.datetime.strptime( date ,'%Y-%m-%d').strftime('%a %d %b %Y')
        except:
            return 'MALFORMED'

    def demux_row( self, row, md=False ):
        return  { 'id': row[0],
                  'title': row[1],
                  'text': markdown(row[2]) if md else row[2].strip(),
                  'date': row[3],
                  'date_str': self.date_str( row[3] ) }

    def entry( self, entry_id, md=False, title=None ):
        if title:
            sql = 'select * from entries where title=?'
            row = self.db.execute( sql, [title] ).fetchone()
        else:
            sql = 'select * from entries where id=?'
            row = self.db.execute( sql, [entry_id] ).fetchone()
        if not row:
            return None
        entry = self.demux_row( row, md )
        return self.apply_tags( [entry] )[0]

    def pack( self, rows, limit ):
        entries = []
        count = 0
        for row in rows:
            if limit:
                if count < 12:
                    entries.append( self.demux_row( row, True ) )
            else:
                entries.append( self.demux_row( row, True ) )
            count += 1
        return [ entries, count ]

    def entries( self, date=None, tag=None, notag=False, terms=None ):
        limit = False
        if date:
            sql = 'select * from entries where date=?'
            rows = self.db.execute( sql, [date] )
        elif tag:
            sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id order by date desc'
            rows = self.db.execute( sql, [tag] )
        elif notag:
            sql = 'select * from entries where id not in (select id from tags)'
            rows = self.db.execute( sql )
        elif terms:
            terms = '%' + terms  + '%'
            sql = 'select * from entries where (title like ? or text like ?)'
            rows = self.db.execute( sql, [ terms, terms ] )
        else:
            sql = 'select * from entries order by date desc'
            rows = self.db.execute( sql )
            limit = True
        [ entries, count ] = self.pack( rows, limit )
        entries = self.apply_tags( entries  )
        if notag:
            self.total_notag = count
        else:
            self.total_entries = count
        return entries

    def stream( self ):
        entries = self.entries()
        tag_set = self.tag_set()
        if not entries:
            msg = "<h1>Unbelievable. No entries yet.</h1>"
        else:
            msg = "%d entries %d tags %s %s"\
                % ( self.total_entries, 
                    self.total_tags,
                    self.img( 'cloud', '/cloud' ),
                    self.img( 'search', '/search' ))
        return render_template( 'index.html', 
                                entries=entries,
                                msg=msg,
                                index=True )

    def cloud( self ):
        entries = self.entries()
        tag_set = self.tag_set()
        notag = self.entries( None, None, True )
        if not entries:
            msg = "<h1>Unbelievable. No tags yet.</h1>"
        else:
            msg = "%d entries %d tags %s <i>%d not tagged %s</i>"\
                % ( self.total_entries,
                    self.total_tags,
                    self.img( 'home', '/' ),
                    self.total_notag,
                    self.img( 'notag', '/notag' ))
        return render_template( 'index.html', tag_set=tag_set, msg=msg )

    def singleton( self, entry_id ):
        entry = self.entry( entry_id, True )
        if not entry:
            return redirect( url_for( 'index' ) )
        return render_template( 'index.html', entries=[ entry ] )

    def dated( self, date ):
        entries = self.entries( date )
        date_str = self.date_str( date )
        msg = "%d dated %s %s" % ( len(entries), date_str,
                                   self.img( 'home', '/' ))
        return render_template( 'index.html', entries=entries, msg=msg )

    def tagged( self, tag ):
        entries = self.entries( None, tag )
        msg = "%d tagged %s %s %s %s"\
            % ( len(entries), 
                tag,
                self.img( 'home', '/' ),
                self.img( 'cloud', '/cloud' ),
                self.img( 'search', '/search' ))
        return render_template( 'index.html', entries=entries, msg=msg )
        
    def notag( self ):
        entries = self.entries( None, None, True )
        msg = "%d not tagged %s %s" % ( len(entries), 
                                        self.img( 'home', '/' ),
                                        self.img( 'cloud', '/cloud' ) )
        return render_template( 'index.html', entries=entries, msg=msg )
        
    def matched( self, terms ):
        found = self.entries( None, None, False, terms )
        msg = "%d matched { %s } %s %s"\
            % ( len(found), 
                terms,
                self.img( 'search', '/search' ),
                self.img( 'home', '/' ))
        return render_template( 'index.html', entries=found, msg=msg )
