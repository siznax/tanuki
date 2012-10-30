"""
dump records tagged 'posted'
"""
__author__ = "siznax"
__version__ = "Oct 2012"

import commands
import sqlite3

def source_db( dbfile ):
    con = sqlite3.connect( dbfile )
    con.execute('pragma foreign_keys = on') # !important
    return con

def target_db( dbfile, schema ):
    try:
        os.remove( dbfile )
        print "removed %s" % ( dbfile ) 
    except:
        pass
    commands.getstatusoutput("sqlite3 %s < %s" % ( dbfile, schema ))
    con = sqlite3.connect( dbfile )
    con.execute('pragma foreign_keys = on') # !important
    return con

def get_tagged( db, tag ):
    try:
        sql = 'select * from entries,tags where tags.name=? and tags.id=entries.id order by date desc'
        return db.execute( sql, [ tag ] )
    except:
        print "DB error"

def push_tags( sdb, sid, tdb, tid ):
    tags = []
    sql = 'select name,date from tags where id=?' 
    for r in sdb.execute( sql, [ sid ] ):
        if not r[0] == "posted":
            sql = 'insert into tags values(?,?,?)'
            tdb.execute( sql, [ tid, r[0], r[1] ] )
            tdb.commit()
            tags.append( r[0] )
    return sorted(tags)

def insert( db, row ):
    sql = 'insert into entries values(?,?,?,?)'
    val = [ row[0], row[1], row[2], row[3] ]
    cur = db.execute( sql, val )
    db.commit()
    return cur.lastrowid

sdb = source_db( "/Users/siznax/Code/tanuki/tanuki.db" )
tdb = target_db( "/tmp/blog.db", "/Users/siznax/Code/tanuki/schema.sql" )

for row in get_tagged( sdb, "posted" ):
    tid = insert( tdb, row )
    tags = push_tags( sdb, row[0], tdb, tid )
    print "%s %s %s %s" % ( tid, row[0], row[1], tags )
