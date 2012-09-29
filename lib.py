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

    def demux_row( self, row, md=False ):
        return  { 'id': row[0],
                  'title': row[1],
                  'text': markdown(row[2]) if md else row[2].strip(),
                  'date': row[3],
                  'date_str': datetime.datetime.strptime(row[3],'%Y-%m-%d').strftime('%a %d %b %Y') }

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

    def entries( self, date=None, tag=None ):
        entries = []
        if date:
            sql = 'select * from entries where date=?'
            rows = self.db.execute( sql, [date] )
        elif tag:
            sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id'
            rows = self.db.execute( sql, [tag] )
        else:
            sql = 'select * from entries order by date desc'
            rows = self.db.execute( sql )
        for row in rows:
            entries.append( self.demux_row( row, True ) )
        entries = self.apply_tags( entries  )
        return entries

    def entries_dated( self, date ):
        entries = self.entries( date )
        date_str = datetime.datetime.strptime( date, '%Y-%m-%d' ).strftime( '%a %d %b %Y' )
        msg = "&#9732; found %d entries dated %s" % ( len(entries), date_str )
        return render_template('index.html', 
                               entries=entries,
                               msg=msg)

    def delete( self, req ):
        sql = 'DELETE from entries WHERE id=?'
        self.db.execute( sql, [req.form['entry_id']] )
        self.con.commit()

