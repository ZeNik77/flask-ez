from flask import Flask, request, jsonify, make_response, redirect, render_template
import subprocess
from db_session import create_session
import users
import hashlib
import time
import random


MAX_GAMES = 9999
ROOM_IDS_RANGE = 10 ** 10
USER_IDS_RANGE = 10 ** 10

db_sess = create_session()

app = Flask(__name__)

def sha512(Password):
    HashedPassword = hashlib.sha512(Password.encode('utf-8')).hexdigest()
    return HashedPassword

def account_check(req):
    a = request.cookies.get('session', 0)

    if a:
        res = db_sess.query(users.User).filter(users.User.session == a).all()
        if len(res) == 1:
            return res[0].glob_id
    return False

def get_username(request):
    id = account_check(request)
    username = db_sess.query(users.User.name).filter(users.User.glob_id == id).first()
    if username:
        return username[0]
    else:
        return ''

@app.route('/')
def index():
    user = {'nickname': 'xd'}
    return render_template('index.html', title='home', user=user)

@app.route('/run_code', methods=['POST'])
def run_code():
    code = request.form['code']
    with open('code.txt', 'w') as f:
        f.write(code)
    out = subprocess.run(['python', 'code.txt'], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
    if not out.stderr:
        print(out.stdout)
        return render_template('index.html', out=out.stdout, err='', code=code)
    else:
        print(out.stderr)
        return render_template('index.html', out='', err=out.stderr, code=code)
    
@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.is_json:
        username = request.json.get('name', 0)
        password = request.json.get('pass', 0)
        res = db_sess.query(users.User).filter(
            users.User.name == username and users.User.hashed_password == password).all()
        if res:
            user = res[0]
            session = sha512(user.hashed_password + str(time.time()))
            user.session = session
            db_sess.commit()
            res = make_response(session)
            res.set_cookie("session", session, max_age=60 * 60 * 24 * 365 * 2)
            return res
    else:
        return render_template('login.html', cur_user=get_username(request))


@app.route('/signup', methods=['POST', 'GET'])
def signup(request):
    if request.is_json:
        username = request.json['name']
        mail = request.json['mail']
        password = request.json['pass']
        usrs = db_sess.query(users.User).filter(users.User.email == mail or users.User.name == username).all()
        if len(usrs) == 0:
            try:
                new = users.User()
                new.glob_id = random.randint(1, USER_IDS_RANGE)
                new.email = mail
                new.rating = 0
                new.name = username
                new.hashed_password = password
                db_sess.add(new)
                db_sess.commit()
            except:
                return 'server error'
            return 'Ok'
        else:
            return 'Failed'
    else:
        return render_template('signup.html', cur_user=get_username(request))


@app.route('/leaderboard', methods=['POST', 'GET'])
def leaderboard():
    leaderboard_data = db_sess.query(users.User.name, users.User.rating).order_by(users.User.rating.desc()).all()
    return render_template('leaderboard.html', leaderboard_data=leaderboard_data, cur_user=get_username(request))


@app.route('/profile', methods=['GET'])
def profile():
    id = account_check(request)
    if id:
        dataxd = db_sess.query(users.User.name, users.User.rating).filter(users.User.glob_id == id).first()
        print(type(dataxd))
        if len(dataxd):
            print('\n\n\n', dataxd, '\n\n\n')
            return render_template('profile.html', data=dataxd, cur_user=get_username(request))
        else:
            return "no data"
    else:
        return redirect('/signup')