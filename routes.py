from flask import Flask, request, url_for, make_response, redirect, render_template
import subprocess
from db_session import create_session
import users
import hashlib
import time


MAX_GAMES = 9999
ROOM_IDS_RANGE = 10 ** 10
USER_IDS_RANGE = 10 ** 10

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

@app.route('/')
def index():
    print('\''+get_username(request)+'\'')
    if get_username(request):
        print('HAHAHA?')
    return render_template('index.html', title='home', cur_user=get_username(request))

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.form['code']
    with open('code.txt', 'w') as f:
        f.write(code)
    out = subprocess.run(['python', 'code.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if not out.stderr:
        print(out.stdout)
        return render_template('index.html', cur_user=get_username(request), out=out.stdout, err='', code=code)
    else:
        print(out.stderr)
        return render_template('index.html', cur_user=get_username(request), out='', err=out.stderr, code=code)
    
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
    return render_template('about.html')