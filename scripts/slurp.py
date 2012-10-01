"""
i used this to slurp up a bunch of text files into the DB
"""
__author__ = "siznax"
__version__ = "Sep 2012"

from dateutil import parser
import commands
import datetime
import glob
import os
import re
import sqlite3

def head( infile, N=4 ):
    with open(infile,"r") as hfile:
        try:
            head = [hfile.next() for x in xrange(N)]
            return unicode(''.join(head),'utf-8')
        except StopIteration:
            return file(infile,'r').read()

def head_date( fname, head ):
    try:
        dstr = re.search("Date:(.*)\n",head).groups()[0]
        dobj = parser.parse(dstr.strip())
    except:
        dobj = datetime.date.fromtimestamp(os.stat(fname)[9])
    return str( dobj.strftime("%Y-%m-%d") )

def head_title( fname, head ):
    try:
        m = re.search("Subject:(.*)\n",head).groups()[0]
        return str(''.join( m )).strip()
    except:
        return fname.split('/')[-1]

def parse( text ):
    found_body = False
    body = ""
    head = ""
    for line in text.split("\n"):
        if found_body:
            body += line + "\n"
        else:
            if not line.strip():
                found_body = True
            else:
                head += line + "\n"
    return {'head':head,'body':body}

def store( files, db, tag ):
    for f in files:
        with open( f, "r" ) as fp:
            blob = parse( unicode( fp.read(), 'utf-8' ))
            title = head_title( f, blob['head'] ) 
            text = blob['body']
            date = head_date( f, blob['head'] ) 
            try:
                sql = 'insert into entries values(?,?,?,?)'
                val = [ None, title, text, date ]
                cur = db.execute( sql, val )
            except sqlite3.IntegrityError:
                sql = 'insert into entries values(?,?,?,?)'
                val = [ None, title+" IMPORT_ERROR", text, date ]
                cur = db.execute( sql, val )
            sql = 'insert into tags values(?,?,?)'
            db.execute( sql, [ cur.lastrowid, tag, date ] )

def init_db( dbfile, schema ):
    try:
        os.remove( dbfile )
    except:
        pass
    commands.getstatusoutput("sqlite3 %s < %s" % ( dbfile, schema ))
    con = sqlite3.connect( dbfile )
    con.execute('pragma foreign_keys = on') # !important
    return con

con = init_db( '/tmp/slurp.db', "/Users/siznax/Code/tanuki/schema.sql" )

top = "/Users/siznax/Code/tanuki/import"
dirs = [ d for d in os.listdir( top ) if os.path.isdir( os.path.join(top,d) ) ]

for tag in dirs:
    files = "%s/%s/*.txt" % ( top, tag ) 
    print tag,
    print files
    store( glob.glob( files ), con.cursor(), tag )

con.commit()
con.close()
