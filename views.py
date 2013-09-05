from flask import render_template, flash, redirect, request, session, g, url_for

from dotabank import app, oid, steam, db
from models import User

# User authentication
@app.route('/login/')
@oid.loginhandler
def login():
    if g.user is not None:
        return redirect(oid.get_next_url())
    return oid.try_login('http://steamcommunity.com/openid')


@oid.after_login
def create_or_login(resp):
    steam_id = long(resp.identity_url.replace("http://steamcommunity.com/openid/id/", ""))
    account_id = int(steam_id & 0xFFFFFFFF)
    g.user = User.query.filter(User.id == int(account_id & 0xFFFFFFFF)).first()

    if not g.user:
        g.user = User(int(account_id & 0xFFFFFFFF), steam.user.profile(steam_id).persona or account_id)

        db.session.add(g.user)
        db.session.commit()
    session['user_id'] = g.user.id
    flash('You are logged in as %s' % g.user.name, "success")
    return redirect(oid.get_next_url())


@app.before_request
def before_request():
    g.user = None
    if 'user_id' in session:
        g.user = User.query.filter(User.id == session['user_id']).first()


@app.route('/logout/')
def logout():
    session.pop('user_id', None)
    return redirect(oid.get_next_url())


# Routes
@app.route('/')
def index():
    return render_template("dotabank.html")


@app.route("/user/<int:_id>")
def user(_id):
    return "abc"
