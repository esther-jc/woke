-- makes tables necessary for woke database
use woke_db;

drop table if exists votes; 
drop table if exists review;
drop table if exists course;
drop table if exists student;
 
create table student (
    username varchar(10) not null,
    primary key (username))
    ENGINE = InnoDB;

create table course (
    cId varchar(9) not null, 
    course_name varchar(50),
    department varchar(4),
    primary key (cId))
    ENGINE = InnoDB;
 
create table review (
    rId int not null auto_increment primary key,
    cId varchar(7) not null,
    `hours` tinyint,
    `remote` enum('yes','no'), 
    attendance enum('mandatory','not mandatory'), 
    how_fun tinyint, 
    professor varchar(30), 
    relevance tinyint,
    downvotes tinyint, 
    upvotes tinyint, 
    date_submitted date,
    write_up text,
    username varchar(10) not null,
    index (username), 
    foreign key (username) references student(username) 
        on update restrict 
        on delete restrict,
    index(cId),
    foreign key (cId) references course (cId) 
        on update restrict 
        on delete restrict)
    engine = InnoDB;
 
create table votes (
    rId int not null,
    username varchar(10) not null,
    updown boolean,
    primary key (rId, username),
    index(rId),
    foreign key (rId) references review (rId)
        on update restrict
        on delete restrict,
    index(username),
    foreign key(username) references student (username)
        on update restrict
        on delete restrict)
    ENGINE = InnoDB;

    -- add syllabus file name column
    alter table review add syllabus varchar(50);
    -- dropped column isbn not needed
    -- (alter table review drop columnn textbook_isbn;)