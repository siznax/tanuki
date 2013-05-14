drop table if exists entries;
create table entries (
       id integer primary key autoincrement,
       title string unique not null, 
       text string unique not null,
       date text not null,
       updated text,
);
create table tags (
       id integer not null,
       name string not null,
       date text not null,
       foreign key(id) references entries(id)
);
