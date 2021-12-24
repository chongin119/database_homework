import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import doctorItems
bp = Blueprint('doctor', __name__)

db = connect_db(databasePATH)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select e_id \
                      from employees \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]
@bp.route('/doctor/?<string:username>', methods=['GET', 'POST'])
def doctor(username):
    if session.get(username) is not None:
        doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('doctor.html', name=username, sidebarItems=doctorItems,doctor=doctor)
    return redirect(url_for('auth.login'))

@bp.route('/doctor/?<string:username>/appointments',methods=['GET', 'POST'])
def appoinments(username):
    doc_id = get_id(db,username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()
    return render_template('doctor_app.html',appointments=appointments)

@bp.route('/doctor/?<string:username>/prescription',methods=['GET', 'POST'])
def prescription(username):
    doc_id = get_id(db, username)
    prescription = db.execute("SELECT date , p.name, p.phone, med_id, med_quantity, med_name,  FROM prescription pre \
                                INNER JOIN patient p ON p.patient_id = pre.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()
    return render_template('doctor_pre.html', prescription=prescription)


