# woke.py contains many helper functions to be used in app.py

import cs304dbi as dbi
import pymysql #for integtrity error
import sys
from datetime import datetime

# ==========================================================
# The functions that do most of the work.

def now():
    '''Returns a string for the current day and time.'''
    now = datetime.now()
    return now.strftime("%Y-%m-%d %H:%M:%S")

def insert(conn,cid,hours,remote,attend,fun,professor,relevance,
text, username):
    '''inserts review info from student into database'''
    curs = dbi.dict_cursor(conn)
    
    curs.execute('''insert into review (cId,hours,remote,
                attendance,how_fun,professor,relevance,write_up,username,
                date_submitted, upvotes, downvotes)
                values (%s,%s,%s,%s,%s,%s,%s,%s,%s, %s, 0, 0)''',
                [cid,hours,remote,attend,fun,professor,relevance,
                text,username, str(now())])
    conn.commit()
    #return rid of the last inserted review (last_insert_id wasn't working)
    curs.execute('''select rId from review where cId = %s and hours=%s 
                and remote=%s and attendance=%s and how_fun=%s and 
                professor=%s and relevance=%s and write_up=%s and username=%s
                and upvotes=0 and downvotes=0''',
                [cid,hours,remote,attend,fun,professor,relevance,
                text,username])
    return curs.fetchone()

def insert_syllabus(conn,rid,syllabus):
    '''inserts syllabus filename of certain rid 
    into review table'''
    curs = dbi.dict_cursor(conn)
    
    nr = curs.execute('''update review
                    set syllabus = %s where rid = %s''',
                [syllabus, rid])
    conn.commit()
    return nr

def get_filename(conn, rid):
    '''gets filename of syllabus of review with 
    specified rid from review table'''
    curs = dbi.dict_cursor(conn)
    curs.execute(
        '''select syllabus from review where rId = %s''',
        [rid])
    row = curs.fetchone()
    return row

def overallCourseAvgs(conn,cId):
    '''Gathers overall course info to display on top of individual
    course page, i.e. hours per week, how fun, relevance to real
    world'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select avg(hours), avg(how_fun), avg(relevance) 
                    from review where `cId` = %s''', [cId])
    return curs.fetchone()

def getRandomCourse(conn):
    '''Returns random course to display on welcome page each time'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select cId,course_name from course 
                    order by rand() limit 1''')
    return curs.fetchone()

def get_course_reviews(conn, cId):
    '''Returns the information for the course of id cId
        and all the reviews for it.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select * from review where `cId` = %s', [cId])
    return curs.fetchall()

def get_course_info(conn, cId):
    '''Returns course name, department, and id'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select * from course where `cId`=%s', [cId])
    return curs.fetchall()[0]

def reviews_sort_fun(conn, cId):
    '''Returns reviews for course cId sorted by how fun the course
        is rated by that review (the most fun to least)'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from review where `cId` = %s 
                    order by how_fun desc''', [cId])
    return curs.fetchall()

def reviews_sort_recent(conn, cId):
    '''Returns reviews for course cId sorted by how recent the reviews are
        (the most recent to least)'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from review where `cId` = %s 
                    order by date_submitted desc''', [cId])
    return curs.fetchall()

def reviews_sort_relevant(conn, cId):
    '''Returns reviews for course cId sorted by how relevant the course
        is rated by that review
        (the most relevant to least)'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select * from review where `cId` = %s 
                    order by relevance desc''', [cId])
    return curs.fetchall()

def insert_usn(conn,usn):
    '''Insert username into student table. if already inserted,
        returns false (does nothing)'''
    curs = conn.cursor()
    try: #try to insert into student table
        nr = curs.execute('''insert into student(username)
         values (%s)''',[usn])
        conn.commit()
        return nr == 1
    except pymysql.IntegrityError as err: #if already inserted, do nothing
        return False

def get_all_departments(conn):
    '''Returns all distinct departments as a list of dictionaries'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select distinct department from course')
    return curs.fetchall()

def get_review_info(conn, rId):
    '''Returns review contents using review id in
    review table, as a list of dictionaries.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select * from review where rId = %s', [rId])
    return curs.fetchone()

def update(conn,rId,cid,hours,remote,attend,fun,prof,
        relev, writeUp):
    '''Returns the name and birthdate of all the entries in
    the person table, as a list of dictionaries.'''
    curs = dbi.dict_cursor(conn)
    nr = curs.execute('''update review 
        set cid = %s, hours = %s, attendance = %s, remote = %s, 
        how_fun = %s, relevance = %s, 
        professor = %s, write_up = %s, date_submitted = %s 
        where rId = %s''', 
        [cid, hours, attend, remote, fun, relev, prof, writeUp,
        str(now()), rId])
    conn.commit()
    return nr

def delete(conn, rid):
    '''Deletes review from review table with 
    matching review id.'''
    curs = dbi.dict_cursor(conn)
    nr = curs.execute('delete from review where rId = %s', [rid])
    conn.commit()
    return nr

def get_my_reviews(conn, usn):
    '''Returns all reviews for logged in user in
    the review table, as a list of dictionaries.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('select *  from review where username = %s', [usn])
    return curs.fetchall()

def insert_vote(conn,rid,usn,upordown):
    '''Insert vote into votes table;
        Upordown = True for upvote, false for downvote'''
    curs = conn.cursor()
    try: #try to insert into vote table
        nr = curs.execute('''insert into votes(rId, username, updown)
                        values (%s, %s, %s)''',[rid, usn, upordown])
        conn.commit()
        return nr == 1
    except pymysql.IntegrityError as err: #if already inserted, do nothing
        return False

def update_total_votes(conn, rid, upordown):
    '''Updates total votes of up/down vote'''
    curs = conn.cursor()
    if upordown: #if upvote, increment upvotes
        #replaces null values with 0
        nr = curs.execute('''update review 
            set upvotes= upvotes + 1 
            where rId = %s''', [rid])
        conn.commit()
    else: #if downvote, increment downvotes
        #replaces null values with 0
        nr = curs.execute('''update review 
            set downvotes= downvotes + 1 
            where rId = %s''', [rid])
        conn.commit()
    return nr

def get_total_votes(conn, rId):
    '''Returns review votes total using review id in
    review table, as a dictionary'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select upvotes, downvotes from review 
        where rId = %s''', [rId])
    return curs.fetchone()

def get_courses_in_dept(conn, department):
    '''Returns the cId, course_name, department of all the 
    entries in the course table, as a list of dictionaries.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select cId, course_name, department 
    from course where department = %s''', [department])
    return curs.fetchall()

def search_is_cId(conn, string):
    '''Returns the cId that exactly matches the string, 
    if it exists.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select cId from course
                            where cId = %s ''', 
                        [string])
    return curs.fetchone()

def search_like_name(conn, string):
    '''Returns the cId, course_name, department of all the matching
    entries in the course table, as a list of dictionaries.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select cId, course_name, department
                            from course
                            where course_name like %s or cid like %s''', 
                        ['%' + string + '%', '%' + string + '%'])
    return curs.fetchall()

""" def get_last_rid(conn):
    '''Returns the last rid as a dictionaries.'''
    curs = dbi.dict_cursor(conn)
    curs.execute('''select last_insert_id()''')
    return curs.fetchone() """

def sort_courses_indept_by(conn, department, by_what):
    '''Returns the courses in a department sorted from the
        most 'by_what' in average to the least 'by_what',
        where 'by_what' can be either 'fun' or 
        'relevant'. If 'by_what' is something else, then
        return None'''
    curs = dbi.dict_cursor(conn)
    courseList = None
    if by_what == "fun":
        curs.execute('''select course.cId, course.course_name, 
        course.department, T.avg_fun from course left join 
        (select cId, avg(how_fun) as 'avg_fun' from review group by cId 
                order by avg(how_fun) desc) as T 
        using (cId) where department = %s order by T.avg_fun desc''', [department])
        courseList = curs.fetchall()
    elif by_what == "relevant":
        curs.execute('''select course.cId, course.course_name, 
        course.department, T.avg_relevant from course left join 
        (select cId, avg(relevance) as 'avg_relevant' from review group by cId) as T 
        using (cId) where department = %s order by T.avg_relevant desc''', [department])
        courseList = curs.fetchall()
    return courseList

# ==========================================================
# This starts the ball rolling, *if* the file is run as a
# script, rather than just being imported.    

if __name__ == '__main__':
    dbi.cache_cnf()   # defaults to ~/.my.cnf
    dbi.use('woke_db')
    conn = dbi.connect()
    # print(sort_courses_indept_by(conn, "CS", "fun"))
    
    