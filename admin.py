import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import adminItems
from forms import DepartmentForm, AppointmentForm
bp = Blueprint('admin', __name__)

db = connect_db(databasePATH)

@bp.route('/patients',methods=['GET','POST'])

def patients():
    patients = db.execute("SELECT * FROM patient").fetchall()
    return render_template('patients.html', patients=patients)

@bp.route('/admin/?<string:username>',methods=['GET','POST'])
def admin(username):
    if session.get(username) is not None:
        return render_template('admin.html', name=username, sidebarItems=adminItems)
    return redirect(url_for('auth.login'))

@bp.route('/add_patient',methods=['GET','POST'])
def add_patient():
    if request.method == 'POST':
        """api to add the patient in the database"""
        request.form = request.get_json(force=True)
        pat_name = request.form['pat_name']
        pat_date = request.form['pat_date']
        pat_passport = request.form['passport']
        pat_gender = request.form['pat_gender']
        pat_phone = request.form['pat_phone']
        pat_email = request.form['pat_email']
        pat_username = request.form['pat_username']
        pat_password = request.form['pat_password']
        error=None
        try:
            request.form['pat_id'] = db.execute('''INSERT INTO patient(name,DOB,passport,gender,phone,email,username,password)
                        VALUES(?,?,?,?,?,?,?,?)''', (
            pat_name, pat_date, pat_passport, pat_gender, pat_phone,pat_email,pat_username,pat_password)).lastrowid
            db.commit()
        except:
            error = 'something got wrong'
        if error is not None:
            flash(error)
        return redirect(url_for('patient.patients'))
    return render_template('add_patient.html')



@bp.route('/patients/<id>',methods=['POST','GET'])
def update_patients(id):
    patient = db.execute("SELECT * FROM patient WHERE pat_id=?", (id,)).fetchall()
    if request.method == 'POST':
        pat_name = request.form['pat_name']
        pat_date = request.form['pat_date']
        pat_passport = request.form['passport']
        pat_gender = request.form['pat_gender']
        pat_phone = request.form['pat_phone']
        pat_email = request.form['pat_email']
        pat_username = request.form['pat_username']
        # pat_password = request.form['pat_password']
        db.execute(
            "UPDATE patient SET name=?,DOB=?,passport=?,gender=?,phone=?,email=?,username=?, WHERE patient_id=?",
            (pat_name, pat_date, pat_passport, pat_gender, pat_phone, pat_email, pat_username))
        db.commit()
        return redirect(url_for('patient.patients'))
    return render_template('update_patient.html',patient=patient)


@bp.route('/admin/?<string:username>/admin_doctors',methods=['GET','POST'])
def admin_doctors(username):
    doctors = db.execute(
         "SELECT department_name, name, passport, gender, phone, username, password, graduate_school, degree, technical_title, specialty \
        FROM doctor NATURAL JOIN department LEFT JOIN employees ON e_id=doc_id \
        ORDER BY department_name ASC"
    ).fetchall()
    return render_template('admin_doctors.html', name=username, sidebarItems=adminItems, doctors=doctors, hav=len(doctors))

@bp.route('/admin/?<string:username>/admin_appointments',methods=['GET','POST'])
def admin_appointments(username):
    appointments = db.execute(
        "SELECT * \
        FROM appointment \
        ORDER BY date DESC"
    ).fetchall()
    return render_template('admin_appointments.html', name=username, sidebarItems=adminItems, appointments=appointments, hav=len(appointments))

@bp.route('/admin/?<string:username>/admin_patients',methods=['GET','POST'])
def admin_patients(username):
    patients = db.execute(
         "SELECT * \
        FROM patient \
        ORDER BY patient_id DESC"
    ).fetchall()
    return render_template('admin_patients.html', name=username, sidebarItems=adminItems, patients=patients, hav=len(patients))

@bp.route('/admin/?<string:username>/admin_departments',methods=['GET','POST'])
def admin_departments(username):
    departments = db.execute(
         "SELECT department_id, department_name, name, numbers \
        FROM department NATURAL JOIN chief LEFT JOIN employees ON e_id=chief_id NATURAL JOIN (SELECT department_id, COUNT(*) AS numbers FROM doctor GROUP BY department_id) \
        ORDER BY department_name DESC"
    ).fetchall()
    return render_template('admin_departments.html', name=username, sidebarItems=adminItems, departments=departments, hav=len(departments))


@bp.route('/admin/?<string:username>/admin_prescriptions',methods=['GET','POST'])
def admin_prescriptions(username):
    prescriptions = db.execute(
        "SELECT * \
        FROM prescription \
        ORDER BY date DESC"
    ).fetchall()
    return render_template('admin_prescriptions.html', name=username, sidebarItems=adminItems, prescriptions=prescriptions, hav=len(prescriptions))

@bp.route('/admin/?<string:username>/admin_records',methods=['GET','POST'])
def admin_records(username):
    records = db.execute(
        "SELECT * \
        FROM medical_record \
        ORDER BY date DESC"
    ).fetchall()
    return render_template('admin_records.html', name=username, sidebarItems=adminItems, records=records, hav=len(records))

@bp.route('/admin/?<string:username>/?<int:d_id>/edit_department',methods=['GET','POST'])
def admin_update_department(username, d_id):
    the_department = db.execute(
        "SELECT department_id, chief_id\
        FROM chief\
        WHERE department_id=?", (d_id,)
    ).fetchall()
    form = DepartmentForm(obj=the_department)
    if form.validate_on_submit():
        de_id = form.de_id.data
        che_id = form.che_id.data
        db.execute(
            "UPDATE chief\
            SET chief_id=?\
            WHERE department_id=?", (che_id, de_id,)
        )
        db.commit()
        flash('You have successfully edited the department.')

        # redirect to the departments page
        return redirect(url_for('admin.admin_departments', username=username))

    form.de_id.data = the_department[0][0]
    form.che_id.data = the_department[0][1]

    return render_template('admin_department.html', username=username, sidebarItems=adminItems, form=form)


@bp.route('/admin/?<string:username>/?<int:app_id>/edit_appointment', methods=['GET','POST'])
def admin_update_appointment(username, app_id):
    app = db.execute(
        "SELECT *\
        FROM appointment\
        WHERE app_id=?", (app_id,)
    ).fetchall()
    form = AppointmentForm(obj=app)
    if form.validate_on_submit():
        date=form.date.data
        pat_id=form.pat_id.data
        de_id=form.de_id.data
        doc_id=form.doc_id.data
        temp=form.temp.data
        symptom=form.symptom.data
        address=form.address.data
        risk=form.risk.data
        db.execute(
            "UPDATE appointment\
            SET date=?, patient_id=?, department_id=?, doc_id=?, temperature=?, symptom=?, address=?, risk=?\
            WHERE app_id=?", (date, pat_id, de_id, doc_id, temp, symptom, address, risk, app_id,)
        )
        db.commit()
        flash('You have successfully edited the appointment.')

        # redirect to the departments page
        return redirect(url_for('admin.admin_appointments', username=username))

    form.date.data = app[0][1]
    form.pat_id.data = app[0][2]
    form.de_id.data = app[0][3]
    form.doc_id.data = app[0][4]
    form.temp.data = app[0][5]
    form.symptom.data = app[0][6]
    form.address.data = app[0][7]
    form.risk.data = app[0][8]

    return render_template('admin_appointment.html', username=username, sidebarItems=adminItems, form=form)

