from flask import Flask,request,flash,session
from flask.helpers import url_for
from flask.templating import render_template
from flask_bootstrap import Bootstrap
from flask import g
from datetime import timedelta
import auth,doctor,patient,appointment,chief,admin


from werkzeug.utils import redirect
from dbfunc import insert_user_pwd,connect_db,disconnect_db,match_user_pwd,get_domain

from sliderbaritem import *

app = Flask(__name__)
databasePATH = "testing.db"
app.config['SECRET_KEY'] = "my_secret_key"
app.config['PERMANENT_SESSION_LIFETIME'] = timedelta(hours=1)
bootstrap = Bootstrap(app)

app.register_blueprint(auth.bp)
app.register_blueprint(doctor.bp)
app.register_blueprint(patient.bp)
app.register_blueprint(appointment.bp)
app.register_blueprint(chief.bp)
app.register_blueprint(admin.bp)





if __name__ == "__main__":
    app.run(port=3000,debug=True)