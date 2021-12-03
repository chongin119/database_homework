from flask import Flask,request,flash,session
from flask.helpers import url_for
from flask.templating import render_template
from flask_bootstrap import Bootstrap
from flask import g
from datetime import timedelta

from werkzeug.utils import redirect
from dbfunc import *


app = Flask(__name__)
databasePATH = "testing.db"
app.config['SECRET_KEY'] = "my_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
bootstrap = Bootstrap(app)

doctorItems = [
                {"isTitle": False,"name":"主頁","icon":"grid-fill","filename":"doctor.html","url":'doctor'},
                {"isTitle": True,"name":"功能"}    
]

@app.route('/',methods=['GET','POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']

        db = connect_db(databasePATH)
        judge = match_user_pwd(db,username,password)
        disconnect_db(db)

        if judge == True:

            if session.get(username) is None:
                session[username] = username
                session.permanent = True

            db = connect_db(databasePATH)
            domain = int(get_domain(db,username))
            disconnect_db(db)
            
            if domain == 0:
                return redirect(url_for('doctor',username = username))
            elif domain == 1:
                return redirect(url_for('doctor',username = username))
            elif domain == 2:
                return redirect(url_for('patient',username = username))
        else:
            flash('login failed!')
            return redirect(url_for('login'))
    return render_template('login.html')

@app.route('/logout')
@app.route('/logout?<string:username>')
def logout(username=None):
    if session.get('username') == username:
        session.pop('username')
    return redirect(url_for('login'))


@app.route('/forget_password')
def forget_password():
    return render_template('forget_password.html')

@app.route('/register' , methods=['GET','POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        repeat_password = request.form['repeat_password']

        if password != repeat_password:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('register'))

        db = connect_db(databasePATH)
        judge = insert_user_pwd(db,username,password)
        disconnect_db(db)

        if judge == True:
            flash('Register Success!')
            return redirect(url_for('login'))
        else:
            return redirect(url_for('register'))
    return render_template('register.html')

@app.route('/patient/?<string:username>',methods=['GET','POST'])
def patient(username):
    if session.get(username) is not None:
        return render_template('patient.html',name = username)
    return redirect(url_for('login'))

@app.route('/doctor/?<string:username>',methods=['GET','POST'])
def doctor(username):
    if session.get(username) is not None:
        
        return render_template('doctor.html',name = username,sidebarItems = doctorItems)
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(debug=True)