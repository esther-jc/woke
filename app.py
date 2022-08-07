# app.py for WOKE webpage to view, submit, edit reviews on Wellesley
# courses after authenticated
from flask import (Flask, render_template, make_response, url_for, request,
                   redirect, flash, session, send_from_directory, jsonify)
from werkzeug.utils import secure_filename
from flask_cas import CAS

app = Flask(__name__)


import cs304dbi as dbi
import woke
import random, os, sys

app.secret_key = ''.join([ random.choice(('ABCDEFGHIJKLMNOPQRSTUVXYZ' +
                                          'abcdefghijklmnopqrstuvxyz' +
                                          '0123456789'))
                           for i in range(20) ])

# This gets us better error messages for certain common request errors
app.config['TRAP_BAD_REQUEST_ERRORS'] = True

# for file upload
app.config['UPLOADS'] = 'uploads'
app.config['MAX_CONTENT_LENGTH'] = 1*1024*1024 # 1 MB

# For CAS
CAS(app)

app.config['CAS_SERVER'] = 'https://login.wellesley.edu:443'
app.config['CAS_LOGIN_ROUTE'] = '/module.php/casserver/cas.php/login'
app.config['CAS_LOGOUT_ROUTE'] = '/module.php/casserver/cas.php/logout'
app.config['CAS_VALIDATE_ROUTE'] = '/module.php/casserver/serviceValidate.php'

app.config['CAS_AFTER_LOGIN'] = 'logged_in'
app.config['CAS_AFTER_LOGOUT'] = 'after_logout'      # doesn't work :-(

#provides login button
@app.route('/')
def pre_login():
    '''Returns rendered pre login template for user to go through CAS
    to access WOKE'''
    return render_template('pre_login.html')

@app.route('/logged_in/')
def logged_in():
    '''Returns redirect to pre login if not logged in,
    or to main welcome page to access WOKE if log in successful'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    flash('successfully logged in!')
    username = session['CAS_USERNAME']
    conn = dbi.connect()
    #add username to db
    woke.insert_usn(conn, username)
    return redirect(url_for('index'))

@app.route('/welcome/')
def index():
    '''Returns redirect to pre login if not logged in,
    or main welcome page if valid'''
    #must login
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    conn = dbi.connect()
    randCourse = woke.getRandomCourse(conn)
    return render_template('main.html',
                            randomId = randCourse['cId'],
                            randomName = randCourse['course_name'],
                            page_title='Welcome to WOKE')

@app.route('/submitreview/', methods=['GET','POST'])
def submit_review():
    '''Returns redirect to pre login if not logged in,
    or general form to submit review if get method,
    or submits review to database and redirects to the 
    individual course page of the submitted review if post'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    username = session["CAS_USERNAME"]

    # get general review form
    if request.method == 'GET':
        return render_template('genform.html',
                               page_title="Course Review Form")
    else: #post/submit form
        try:
            conn = dbi.connect()
            cid = request.form.get('courseID')
            if not woke.search_is_cId(conn,cid):
                flash("invalid course ID")
                return render_template('genform.html',
                                page_title="Course Review Form")
            hours = int(request.form.get('hours'))
            attend = request.form.get('attend')
            remote = request.form.get('remote')
            fun = int(request.form.get('fun'))
            relev = int(request.form.get('relevance'))
            prof = request.form.get('prof')
            writeUp = request.form.get('textInput')

            #insert all non-file info into db
            rid_dict = woke.insert(conn,cid,hours,remote,attend,fun,prof,
            relev, writeUp, username)
            
            #get the rId of that review that was just inserted
            curr_rid = rid_dict['rId']
            
            #save uploaded file to that same review
            f = request.files['syllabus']
            user_filename = f.filename
            ext = user_filename.split('.')[-1]
            if ext != '':
                filename = secure_filename('{}.{}'.format(curr_rid,ext))
                pathname = os.path.join(app.config['UPLOADS'],filename)
                f.save(pathname)
                woke.insert_syllabus(conn, curr_rid, filename)
            
            flash('Review Submitted!')
            #redirects to the course page
            return redirect(url_for('course',cid=cid))
            flash('Upload successful')
                                   
        except Exception as err:
            flash('Upload failed {why}'.format(why=err))
            return render_template('genform.html',
            page_title="Course Review Form")

@app.route('/syllabus/<rid>')
def download(rid):
    conn = dbi.connect()
    row = woke.get_filename(conn, rid)

    if row['syllabus'] is None:
        flash('No syllabus for {}'.format(rid))
        review_info = woke.get_review_info(conn, rid)

        cId = review_info['cId']
        return redirect(url_for('course', cid = cId))

    return send_from_directory(app.config['UPLOADS'],row['syllabus'])

@app.route('/course/<cid>/', methods=["GET", "POST"])
def course(cid):
    '''Returns redirect to pre login if not logged in,
    or renders individual course page if get method,
    or sorts reviews by criteria if post method (w/rendered template)'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    cid = cid.upper()
    conn = dbi.connect()
    course_details = woke.get_course_info(conn, cid)
    course_reviews = []
    # sort reviews by criteria
    if request.method == "POST":
        sort_by = request.form.get("sort_by")
        if sort_by == "how fun":
            course_reviews = woke.reviews_sort_fun(conn, cid)
        elif sort_by == "how recent":
            course_reviews = woke.reviews_sort_recent(conn, cid)
        elif sort_by == "how relevant":
            course_reviews = woke.reviews_sort_relevant(conn, cid)
    else: # get method
        course_reviews = woke.get_course_reviews(conn, cid)
    #individual course page display
    #overall averages collected from reviews on course
    avgHrs = (woke.overallCourseAvgs(conn,cid))['avg(hours)']
    avgFun = (woke.overallCourseAvgs(conn,cid))['avg(how_fun)']
    avgRel = (woke.overallCourseAvgs(conn,cid))['avg(relevance)']
    if avgHrs:
        avgHrs = round(avgHrs,1)
    if avgFun:
        avgFun = round(avgFun,1)
    if avgRel:
        avgRel = round(avgRel,1)

    return render_template('course.html',
        page_title=str("Course - " + course_details['cId']),
        course_details= course_details,
        course_reviews= course_reviews,
        hrswk = avgHrs,
        howfun = avgFun,
        relrealworld = avgRel)

@app.route('/departments/')
def all_departments():
    '''Returns redirect to pre login if not logged in,
    or shows all departments/renders the template'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login')) 
    conn = dbi.connect()
    depts = woke.get_all_departments(conn)
    return render_template('alldepartments.html', 
    page_title = "Departments", departments = depts)

@app.route('/updatereview/', methods=['GET','POST'])
def update_review():
    '''Returns redirect to pre login if not logged in,
    or if get method redirects to see all reviews
    or if post option to update/delete review, then displays updated all
    my reviews'''
    if 'CAS_USERNAME' not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    username = session['CAS_USERNAME']
    if request.method == 'GET':
        return redirect(url_for('my_reviews'))
    else:
        conn = dbi.connect()
        button = request.form['submit']
        rid = request.form.get('rId')
        if button == 'Update':
            cid = request.form.get('courseID')
            hours = int(request.form.get('hours'))
            attend = request.form.get('attend')
            remote = request.form.get('remote')
            fun = int(request.form.get('fun'))
            relev = int(request.form.get('relevance'))
            prof = request.form.get('prof')
            writeUp = request.form.get('textInput')

            #update review 
            woke.update(conn,rid,cid,hours,remote,attend,fun,prof,
            relev, writeUp)
            flash('Review Updated!')

        if button == 'Delete':
            woke.delete(conn, rid)
            flash('Review Deleted!')
        
        return redirect(url_for('my_reviews'))

#shows only logged in user's reviews
@app.route('/myreviews/', methods=["GET", "POST"])
def my_reviews():
    '''Returns redirect to pre login if not logged in,
    or renders all of my reviews template if get
    or renders update form if post (clicked edit button on review)'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    username = session['CAS_USERNAME']
    
    conn = dbi.connect()
    if request.method == 'GET':
        myrevs = woke.get_my_reviews(conn, username)
        return render_template('myreviews.html', 
            page_title='My Reviews', my_reviews = myrevs)
    else: #post to update review
        rId = request.form['rId']
        
        #get review information to pass into template
        review = woke.get_review_info(conn, rId)

        cid = review['cId']
        hours = review['hours']
        #attend and remote are yes/no to populate radio buttons accordingly
        attend = review['attendance']
        remote = review['remote']
        fun = review['how_fun']
        relev = review['relevance']
        prof = review['professor']
        writeUp = review['write_up']

        #return prepopulated update page
        return render_template('update.html', page_title = 'Update', 
                    rId = rId, cId = cid, hours = hours, 
                    amode = attend, rmode = remote, fun = fun, 
                    relevance = relev, professor = prof, text = writeUp)


@app.route('/voting/', methods=['POST'])
def vote():
    '''Increments or decrements the global counters via an Ajax request. 
        Response is both counter values.'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    data = request.form
    conn = dbi.connect()
    rid = data.get('rid')
    
    #insert vote into votes table
    username = session['CAS_USERNAME']     
    if data.get('up'):
        upordown = True    #true for upvote, false for down
    else:
        upordown = False

    #if already voted, voted = false
    voted = woke.insert_vote(conn, rid, username, upordown)

    #if vote was updated, update total vote count
    if voted:
        totalup = woke.update_total_votes(conn, rid, upordown)
    
    #retrieve updated vote count and send back to browser
    votecount = woke.get_total_votes(conn, rid)
    upvotes = votecount['upvotes']
    downvotes = votecount['downvotes']
    return jsonify({'rid': rid, 'up': upvotes, 'down': downvotes})

@app.route('/department/<department>/', methods = ['GET', 'POST'])
def courses_in_dept(department):
    '''Returns redirect to pre login if not logged in,
    or renders all courses in department template'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    conn = dbi.connect()
    classes = []
    if request.method == "POST":
        sort_by = request.form.get("sort_by")
        classes = woke.sort_courses_indept_by(conn, department, sort_by)
    else:
        classes = woke.get_courses_in_dept(conn, department)
    return render_template('department.html', classList = classes,
            page_title = str(department) + "Department")

@app.route('/search/', methods=["GET"])
def search():
    '''Returns redirect to pre login if not logged in,
    or searches based on input for matching/like course ID
    or course name'''
    if 'CAS_USERNAME'  not in session:
        flash("Please log in first!")
        return redirect(url_for('pre_login'))
    
    #retrieve class that matches query
    conn = dbi.connect()
    classList = woke.search_like_name(conn, request.args['search'])

    #flashes if there are no matches
    if len(classList) == 0:
        flash("No such course! :-(")
        randCourse = woke.getRandomCourse(conn)
        return render_template("main.html",
                            randomId = randCourse['cId'],
                            randomName = randCourse['course_name'],
                            page_title="Welcome to WOKE")
    
    #if only one course, go directly to course page
    elif len(classList) == 1:
        return redirect(url_for('course', cid = classList[0]['cId']))#?
    else:
        #else go the searchdata and list all applicable classes
        return render_template('searchdata.html',
                                classList=classList, page_title="Search Result")
        
@app.before_first_request
def init_db():
    dbi.cache_cnf()
    dbi.use('woke_db')

if __name__ == '__main__':
    import sys, os
    if len(sys.argv) > 1:
        port=int(sys.argv[1])
        if not(1943 <= port <= 1952):
            print('For CAS, choose a port from 1943 to 1952')
            sys.exit()
    # if len(sys.argv) > 1:
    #     # arg, if any, is the desired port number
    #     port = int(sys.argv[1])
    #     assert(port>1024)
    else:
        port = os.getuid()
    app.debug = True
    app.run('0.0.0.0',port)