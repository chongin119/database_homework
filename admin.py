import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat
from sliderbaritem import adminItems
bp = Blueprint('admin', __name__)

db = connect_db(databasePATH)

def get_dept(db, id):
    department_id, department_name = db.execute("SELECT d.department_id, department_name \
                                From doctor d INNER JOIN department de ON de.department_id = d.department_id \
                                WHERE doc_id=?",(id,)).fetchone()
    return department_id,department_name

@bp.route('/admin/?<string:username>',methods=['GET','POST'])
def admin(username):
    if session.get(username) is not None:
        # doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('admin.html',name=username, sidebarItems=adminItems)
    return redirect(url_for('auth.login'))

@bp.route('/admin/?<string:username>/patients',methods=['GET','POST'])

def patients(username):
    patients = db.execute("SELECT * FROM patient").fetchall()
    return render_template('admin_patients.html', patients=patients,name=username,sidebarItems=adminItems)

@bp.route('/admin/?<string:username>/add_patient',methods=['GET','POST'])

def add_patient(username):
    if request.method == 'POST':
        """api to add the patient in the database"""
        real_name = request.form['realname']
        DOB = request.form['DOB']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        password = request.form['password']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.patients',username=username))

        request.form['pat_id'] = db.execute('''INSERT INTO patient(name,DOB,passport,gender,phone,email,username,password)
                    VALUES(?,?,?,?,?,?,?,?)''', (
        real_name, DOB, passport, gender, phone,email,user,password)).lastrowid
        login_id = db.execute('''INSERT INTO login_inf(username, password, domain)
                    VALUES(?,?,?)''',(user,password,2)).lastrowid
        db.commit()
        flash('Successfully add patient')
        return redirect(url_for('admin.patients'))

    return render_template('admin_add_patient.html',name=username,sidebarItems=adminItems)



@bp.route('/admin/?<string:username>/patients/<id>',methods=['POST','GET'])
def update_patient(username,id):
    # 待修改的病人的数据
    patient_id = id
    patient_inf = db.execute("SELECT * FROM patient WHERE pat_id=?", (id,)).fetchone()
    old_username = patient_inf[7]
    if request.method == 'POST':
        real_name = request.form['realname']
        DOB = request.form['DOB']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        password = request.form['password']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.patients',username=username))
        if password != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, password, old_username))
            db.execute(
                "UPDATE patient SET name=?, DOB=?,passport=?,gender=?,phone=?,email=?,username=?,password=? \
                WHERE patient_id=?",
                (real_name,DOB, passport, gender,phone, email, user, password, patient_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE patient SET name=?, DOB=?,passport=?,gender=?,phone=?,email=?,username=? \
                WHERE patient_id=?",
                (real_name, DOB, passport, gender, phone, email, user, patient_id))
            db.commit()
        flash('Successfully modified information')
        return redirect(url_for('admin.patients'))
    return render_template('admin_update_patient.html',patient=patient_inf,name=username,sidebarItems=adminItems)

@bp.route('/admin/?<string:username>/delete_patient/<id>', methods=['GET', 'POST'])
def delete_patient(username, id):
    patient_id = id
    db.execute("DELETE FROM appointment WHERE patient_id=?", (patient_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from patient WHERE patient_id=?)", (patient_id,))
    db.execute("DELETE FROM patient WHERE patient_id=?", (patient_id,))
    db.commit()
    return redirect(url_for('admin.patients',username=username))

@bp.route('/admin/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    # 找出全部医生，不包括科长
    # 格式为(医生id,医生姓名，电话，邮箱，科室)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email, department_name
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id
                                    INNER JOIN department de ON d.department_id = de.department_id
                                    WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                ''', ).fetchall()

    return render_template('admin_doctors.html',name=username,  sidebarItems=adminItems, doctors=doctors)



@bp.route('/admin/?<string:username>/add_doctor',methods=['GET','POST'])
def add_doctor(username):
    # 给出科室信息，用于选择医生所属科室
    departments = db.execute("SELECT * FROM department").fetchall()

    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['password']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']
        department = request.form['department']

        department_id = db.execute('''SELECT department_id FROM department WHERE department_name = ?''',
                                   (department,)).fetchone()[0]
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('chief.doctors', username=username))
        e_id = db.execute('''
                    INSERT INTO employees(name,passport,gender,phone,email,username,password,
                    graduate_school,degree,technical_title,specialty) VALUES(?,?,?,?,?,?,?,?,?,?,?)'''
                   , (name,passport,gender,phone,email,user,pwd,graduate_school,degree,technical_title,specialty)).lastrowid
        db.execute('''
                            INSERT INTO doctor(doc_id,department_id) VALUES(?,?)'''
                   , (e_id,department_id))
        login_id = db.execute('''
                    INSERT INTO login_inf(username,password) VALUES(?,?)'''
                   , (user, pwd)).lastrowid

        db.commit()

        flash('Successfully add doctor')
        return redirect(url_for('admin.doctors', username=username))

    return render_template('chief_add_doctor.html',name=username,departments=departments)


@bp.route('/admin/?<string:username>/update_doctor/<id>', methods=['GET', 'POST'])
def update_doctor(username, id):
    doc_id = id
    department_id, department_name = get_dept(db, doc_id)
    doctor_inf = db.execute('''SELECT * FROM employees WHERE e_id=?'''
                            , (doc_id,))
    if request.method == "POST":
        name = request.form['name']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        pwd = request.form['password']
        repwd = request.form['repwd']
        graduate_school = request.form['school']
        degree = request.form['degree']
        technical_title = request.form['title']
        specialty = request.form['specialty']

        old_username = doctor_inf[6]
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('admin.doctors',username=username))
        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.doctors'))
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, old_username))
            db.execute(
                "UPDATE employees SET name=?,passport=?,gender=?,phone=?,email=?,username=?,password=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (name,passport,phone,gender, email, user, pwd, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty,doc_id))
            db.commit()
        flash('Successfully modified information')
        return redirect(url_for('admin.doctors', username=username))

    return render_template('admin_update_doctor.html', name=username,doctor_inf=doctor_inf)

@bp.route('/chief/?<string:username>/delete_doctor/<id>', methods=['GET', 'POST'])
def delete_doctor(username, id):
    doc_id = id

    db.execute("DELETE FROM prescription WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM medical_record WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM appointment WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from employees WHERE e_id=?)", (doc_id,))
    db.execute("DELETE FROM doctor WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM employees WHERE e_id=?", (doc_id,))

    db.commit()
    return redirect(url_for('chief.doctors',username=username))