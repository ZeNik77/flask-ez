from flask import Flask, request, url_for, make_response, redirect, render_template
import subprocess
from db_session import create_session
import users
import topics
import tasks
import hashlib
import time
import threading
import timeit

MAX_GAMES = 9999
ROOM_IDS_RANGE = 10 ** 10
USER_IDS_RANGE = 10 ** 10
DONE = False

db_sess = create_session()

app = Flask(__name__)

def sha512(Password):
    HashedPassword = hashlib.sha512(Password.encode('utf-8')).hexdigest()
    return HashedPassword

def account_check(request):
    a = request.cookies.get('session', 0)
    if a:
        res = db_sess.query(users.User).filter(users.User.session == a).all()
        if len(res) == 1:
            return res[0].glob_id
    return False

def get_username(request):
    id = account_check(request)
    username = db_sess.query(users.User.name).filter(users.User.glob_id == id).first()
    #print('\''+username+'\'')
    if username:
        return username[0]
    else:
        return ''
    
def get_user(id):
    return db_sess.query(users.User).filter(users.User.glob_id == id).first()

@app.route('/')
def index():
    return render_template('index.html', cur_user=get_username(request))

def func(name):
    global DONE
    DONE = subprocess.run(['python', name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    

def run(name, max_time):
    global DONE
    cur_time = time.time()
    out = ''
    thread = threading.Thread(target=func, args=(['code.txt']))
    thread.start()
    print(max_time)
    while time.time() - cur_time < max_time:
        pass
    del thread
    if DONE:
        out = DONE
        DONE = False
        if not out.stderr:
            return [out.stdout, '']
        else:
            return ['', out.stderr]
    else:
        return ['', 'TIME LIMIT EXCEEDED']


@app.route('/run_code', methods=['GET', 'POST'])
def run_code():
    if request.method == 'POST':
        code = request.form['code'] 
        with open('code.txt', 'w') as f:
            f.write(code)
        out = run('code.txt', 3)
        if not out[1]:
            print(out[0])
            return render_template('run_code.html', cur_user=get_username(request), out=out[0], err='', code=code)
        else:
            print(out[1])
            return render_template('run_code.html', cur_user=get_username(request), out='', err=out[1], code=code)
    return render_template('run_code.html', title='home', cur_user=get_username(request))

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        user = db_sess.query(users.User).filter(users.User.name == username and users.User.password == password).first()
        if user:
            session = sha512(user.password + str(time.time()))
            user.session = session
            db_sess.commit()
            res = make_response(redirect('/'))
            res.set_cookie('session', session, max_age = 2 * 365 * 24 * 3600)
            return res
    return render_template('login.html', cur_user=(get_username(request)))


@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        
        all_users = db_sess.query(users.User).all()
        if all_users:
            last_id = all_users[-1].glob_id
        else:
            last_id = 0
        new_user = users.User(name=username, email=email, password=sha512(password), glob_id=last_id + 1, about='xd')
        db_sess.add(new_user)
        db_sess.commit()
        return redirect(url_for('index'))
    return render_template('signup.html', cur_user=get_username(request))


@app.route('/leaderboard', methods=['POST', 'GET'])
def leaderboard():
    leaderboard_data = db_sess.query(users.User.name, users.User.rating).order_by(users.User.rating.desc()).all()
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data, cur_user=get_username(request))


@app.route('/profile', methods=['GET', 'POST'])
def profile():
    id = account_check(request)
    if id:
        if request.method == 'POST':
            if 'logout' in request.form:
                user = db_sess.query(users.User).filter(users.User.glob_id == id).first()
                if user:
                    user.session = ''
                    db_sess.commit()
                    # print('\n\n\nhere\n\n\n')
                    return redirect('/login')
            else:
                return redirect('/edit_profile')
        else:
            user = db_sess.query(users.User.name, users.User.rating, users.User.about, users.User.email).filter(
                users.User.glob_id == id).first()
            # print(type(user))
            if len(user):
                # print('\n\n\n', dataxd, '\n\n\n')
                return render_template('profile.html', cur_user=user[0], rating=user[1], about=user[2], email=user[3])
            else:
                return "no data"
    else:
        return redirect('/signup')


@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    id = account_check(request)
    if id:
        user = db_sess.query(users.User).filter(users.User.glob_id == id).first()
        if request.method == 'POST':
            if 'confirm' in request.form:
                if user:
                    user.name = request.form['name']
                    user.about = request.form['about']
                    db_sess.commit()
                    return redirect('/profile')
                else:
                    return redirect('/profile')
            if 'cancel' in request.form:
                return redirect('/profile')
        print('\n\n\n', user.name, '\n\n\n')
        return render_template('edit_profile.html', cur_user=user.name, about=user.about, email=user.email,
                               rating=user.rating)

@app.route('/about', methods=['GET'])
def about():
    return render_template('about.html', cur_user=get_username(request))


@app.route('/courses', methods=['GET', 'POST'])
def courses():
    if request.method == 'POST':
        pass
    data = db_sess.query(topics.Topic).all()
    return render_template('topics.html', cur_user=get_username(request), theme='Темы', title='Все темы', data=data)

@app.route('/courses/course', methods=['GET', 'POST'])
def course():
    if request.method == 'POST':
        pass
    id = request.values.get('course_id', 0)
    topic = db_sess.query(topics.Topic).filter(topics.Topic.glob_id == id).all()
    if topic:
        topic = topic[0]
        data = db_sess.query(tasks.Task).filter(tasks.Task.topic_id == topic.id).all()
        return render_template('topic.html', cur_user=get_username(request), theme=topic.topic, title=topic.topic, description=topic.description, data=data)
    else:
        return redirect('/courses')

@app.route('/courses/task', methods=['GET', 'POST'])
def task():
    if request.method == 'POST':
        pass
    id = request.values.get('task_id', 0)
    print(id)
    task = db_sess.query(tasks.Task).filter(tasks.Task.glob_id == id).one()
    if task:
        return render_template('task.html', task=task.task, description=task.description, cur_user=get_username(request), title=task.task)
    else:
        return redirect('/courses')

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        if 'confirm_topic' in request.form:
            topic = request.form['topic']
            description = request.form['description']
            all_topics = db_sess.query(topics.Topic).all()
            if all_topics:
                id = all_topics[-1].glob_id
            else:
                id = 0
            id += 1
            new_topic = topics.Topic(glob_id=id, topic=topic, description=description)
            db_sess.add(new_topic)
            db_sess.commit()
        if 'confirm_task' in request.form:
            topic_id = request.form['topic_id']
            task_name = request.form['task']
            description = request.form['description']
            all_tasks = db_sess.query(tasks.Task).all()
            if all_tasks:
                id = all_tasks[-1].glob_id
            else:
                id = 0
            task = tasks.Task(glob_id=id+1, topic_id=topic_id, task=task_name, description=description)
            db_sess.add(task)
            db_sess.commit()
        return redirect(url_for('admin'))
    id = account_check(request)
    user = get_user(id)
    try:
        if user.glob_id == 1:
            return render_template('admin.html', user=user, cur_user=get_username(request))
        else:
            return 'слыш тебе сюда нельзя'
    except Exception as e:
        return 'слыш тебе сюда нельзя'