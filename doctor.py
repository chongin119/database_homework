import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import doctorItems
bp = Blueprint('doctor', __name__)

db = connect_db(databasePATH)
@bp.route('/doctor/?<string:username>', methods=['GET', 'POST'])
def doctor(username):
    if session.get(username) is not None:
        doctor = db.execute("SELECT * FROM doctor WHERE username=?", (username,)).fetchall()
        return render_template('doctor.html', name=username, sidebarItems=doctorItems,doctor=doctor)
    return redirect(url_for('auth.login'))


