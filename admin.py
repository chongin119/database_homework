import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat, log_write
from sliderbaritem import adminItems
import datetime
import required_search as rs
bp = Blueprint('admin', __name__)

db = connect_db(databasePATH)

def get_dept(db, id):
    department_id, department_name = db.execute("SELECT d.department_id, department_name \
                                From doctor d INNER JOIN department de ON de.department_id = d.department_id \
                                WHERE doc_id=?",(id,)).fetchone()
    return department_id,department_name

def get_id2pname(db,id):
    cur = db.cursor()
    tt = cur.execute("select name \
                              from patient \
                              where patient_id = '%s'" % id)
    for i in tt:
        return i[0]

def get_eid2name(db, id):
    cur = db.cursor()
    tt = cur.execute("select name \
                                  from employee \
                                  where e_id = '%s'" % id)
    for i in tt:
        return i[0]

@bp.route('/admin/?<string:username>',methods=['GET','POST'])
def admin(username):
    if session.get(username) is not None:
        # doctor = db.execute("SELECT * FROM employees WHERE username=?", (username,)).fetchall()
        return render_template('admin.html',name=username, sidebarItems=adminItems)
    return redirect(url_for('auth.login',username = username))

@bp.route('/admin/?<string:username>/patients',methods=['GET','POST'])
def patients(username):
    patients = db.execute("SELECT * FROM patient").fetchall()
    log_write(user=username, action='visit', dist='patient')
    patdic = {}
    for i in patients:
        patdic[i[0]] = [i[1],i[2],i[3],i[4],i[5],i[6],i[7],i[8]]
    return render_template('admin_patients.html', patients=patdic,name=username,sidebarItems=adminItems,hav=len(patients))

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
        password = request.form['pwd']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('admin.patients',username=username))

        pat_id = db.execute('''INSERT INTO patient(name,DOB,passport,gender,phone,email,username,password)
                    VALUES(?,?,?,?,?,?,?,?)''', (
        real_name, DOB, passport, gender, phone,email,user,password)).lastrowid
        login_id = db.execute('''INSERT INTO login_inf(username, password, domain)
                    VALUES(?,?,?)''',(user,password,2)).lastrowid
        log_write(user=username, action='add', dist='patient')
        db.commit()
        flash('Successfully add patient')
        return render_template('loading.html')

    return render_template('admin_patient_add_working.html',name=username)



@bp.route('/admin/?<string:username>/update_patients/<id>',methods=['POST','GET'])
def update_patient(username,id):
    # ???????????????????????????
    patient_id = id
    patient_inf = db.execute("SELECT * FROM patient WHERE patient_id=?", (id,)).fetchone()
    old_username = patient_inf[7]
    patname = get_id2pname(db,id)

    if request.method == 'POST':
        real_name = request.form['realname']
        DOB = request.form['DOB']
        passport = request.form['passport']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        user = request.form['username']
        password = request.form['pwd']

        if check_repeat(db, user) and old_username != user:
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
            log_write(user=username, action='edit', dist='patient')
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
        return render_template('loading.html')

    return render_template('admin_patient_change_working.html',allinf=patient_inf,name=username,patname = patname)

@bp.route('/admin/?<string:username>/delete_patient/<id>', methods=['GET', 'POST'])
def delete_patient(username, id):
    patient_id = id
    db.execute("DELETE FROM appointment WHERE patient_id=?", (patient_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from patient WHERE patient_id=?)", (patient_id,))
    db.execute("DELETE FROM patient WHERE patient_id=?", (patient_id,))
    log_write(user=username, action='delete', dist='patient')
    log_write(user=username, action='delete', dist='appointment')
    db.commit()
    return render_template('loading.html')

################################?????????
@bp.route('/admin/?<string:username>/doctors',methods=['GET','POST'])
def doctors(username):
    # ??????????????????
    # ?????????(??????id,???????????????????????????????????????)
    doctors = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email, department_name, graduate_school, degree
                                    , technical_title, specialty
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id
                                    INNER JOIN department de ON d.department_id = de.department_id  
                                ''', ).fetchall()
    log_write(user=username, action='visit', dist='employees')
    log_write(user=username, action='visit', dist='department')
    patdic = {}
    for i in doctors:
        patdic[i[0]] = [i[1], i[2], i[3], i[4], i[5], i[6], i[7], i[8]]
    return render_template('admin_doctors.html', patients=patdic, name=username, sidebarItems=adminItems,
                           hav=len(doctors))



@bp.route('/admin/?<string:username>/add_doctor',methods=['GET','POST'])
def add_doctor(username):
    # ???????????????????????????????????????????????????
    departments = db.execute("SELECT * FROM department").fetchall()
    deptdic = {}
    for i in departments:
        deptdic[i[0]] = i[1]
    if request.method == "POST":
        name = request.form['realname']
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
        department_id = request.form['department']

        if check_repeat(db, user):
            flash('The username already exists')
            return redirect(url_for('chief.doctors', username=username))
        e_id = db.execute('''
                    INSERT INTO employees(name,passport,gender,phone,email,username,password,
                    graduate_school,degree,technical_title,specialty) VALUES(?,?,?,?,?,?,?,?,?,?,?)'''
                   , (name,passport,gender,phone,email,user,pwd,graduate_school,degree,technical_title,specialty)).lastrowid
        log_write(user=username, action='add', dist='employees')
        db.execute('''
                            INSERT INTO doctor(doc_id,department_id) VALUES(?,?)'''
                   , (e_id,department_id))
        login_id = db.execute('''
                    INSERT INTO login_inf(username,password) VALUES(?,?)'''
                   , (user, pwd)).lastrowid

        db.commit()

        flash('Successfully add doctor')
        return render_template('loading.html')

    return render_template('admin_add_doctor.html',name=username,deptdic=deptdic)


@bp.route('/admin/?<string:username>/update_doctor/<id>', methods=['GET', 'POST'])
def update_doctor(username, id):
    doc_id = id
    department_id, department_name = get_dept(db, doc_id)
    doctor_inf = db.execute('''SELECT * FROM employees WHERE e_id=?'''
                            , (doc_id,)).fetchone()
    # ???????????????????????????????????????
    departments = db.execute('''SELECT department_id,department_name FROM department'''
                            ).fetchall()
    deptdic = {}
    for i in departments:
        deptdic[i[0]] = i[1]
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
        department_id = request.form['department']

        old_username = doctor_inf[6]
        if check_repeat(db, user) and user != old_username:
            flash('The username already exists')
            return redirect(url_for('admin.doctors'))
        if pwd != "":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, old_username))
            db.execute(
                "UPDATE employees SET name=?,passport=?,gender=?,phone=?,email=?,username=?,password=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (name,passport,phone,gender, email, user, pwd, graduate_school, degree, technical_title, specialty,doc_id))
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, old_username))
            db.execute(
                "UPDATE employees SET phone=?,email=?,username=?,graduate_school=?\
                , degree=?, technical_title=?,specialty=?\
                 WHERE e_id=?",
                (phone, email, user, graduate_school, degree, technical_title, specialty,doc_id))
        db.execute('''
                               UPDATE doctor SET department_id=?
                               WHERE doc_id = ?
                               ''', (department_id, doc_id))
        log_write(user=username, action='edit', dist='employees')
        log_write(user=username, action='edit', dist='department')
        db.commit()
        flash('Successfully modified information')
        return render_template('loading.html')

    return render_template('admin_update_doctor.html', name=username,allinf=doctor_inf ,deptdic=deptdic,department_name=department_name)

@bp.route('/admin/?<string:username>/delete_doctor/<id>', methods=['GET', 'POST'])
def delete_doctor(username, id):
    doc_id = id

    db.execute("DELETE FROM prescription WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM medical_record WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM appointment WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM login_inf WHERE username=(SELECT username from employees WHERE e_id=?)", (doc_id,))
    db.execute("DELETE FROM doctor WHERE doc_id=?", (doc_id,))
    db.execute("DELETE FROM employees WHERE e_id=?", (doc_id,))
    log_write(user=username, action='delete', dist='prescription')
    log_write(user=username, action='delete', dist='records')
    log_write(user=username, action='delete', dist='appointment')
    log_write(user=username, action='delete', dist='employees')
    db.commit()
    return render_template('loading.html')

@bp.route('/admin/?<string:username>/departments',methods=['GET','POST'])
def departments(username):

    # ???????????????????????????????????????
    # ?????????(??????id,???????????????????????????????????????,??????_id,????????????)
    chief_departments = db.execute('''
                                    SELECT e_id,e.name,e.phone,e.email, department_name,d.department_id,description
                                    FROM employees e 
                                    INNER JOIN doctor d ON d.doc_id = e_id
                                    INNER JOIN department de ON d.department_id = de.department_id
                                    WHERE e_id IN (SELECT chief_id FROM chief)  
                                ''', ).fetchall()
    log_write(user=username, action='visit', dist='chief')
    log_write(user=username, action='visit', dist='department')
    log_write(user=username, action='visit', dist='employees')

    patdic = {}
    for i in chief_departments:
        patdic[i[0]] = [i[1], i[2], i[3], i[4], i[5], i[6]]
    return render_template('admin_departments.html', patients=patdic, name=username, sidebarItems=adminItems,
                           hav=len(chief_departments))


@bp.route('/admin/?<string:username>/add_department',methods=['GET','POST'])
def add_department(username):
    # ????????????????????????????????????????????????
    candidate_chief = db.execute('''
                                        SELECT e_id,e.name
                                        FROM employees e 
                                        WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                    ''', ).fetchall()
    chiefdic = {}
    for i in candidate_chief:
        chiefdic[i[0]] = i[1]
    if request.method == "POST":
        name = request.form['dname']
        description = request.form['description']
        chief_id = request.form['chief']

        department_id = db.execute('''
        INSERT INTO department(department_name,description)
        VALUES(?,?)
        ''', (name,description)).lastrowid

        log_write(user=username, action='add', dist='department')
        db.execute('''
                INSERT INTO chief(chief_id,department_id)
                VALUES(?,?)
                ''', (chief_id, department_id))
        log_write(user=username, action='add', dist='chief')
        db.execute('''
                        UPDATE doctor SET department_id=?
                        WHERE doc_id = ?
                        ''', (department_id, chief_id))
        db.commit()

        flash('Successfully add department')
        return render_template('loading.html')

    return render_template('admin_add_department.html',name=username,chiefdic=chiefdic)


@bp.route('/admin/?<string:username>/update_department/<id>', methods=['GET', 'POST'])
def update_department(username, id):
    department_id = id
    # ??????????????????????????????(??????id???????????????????????????????????????id???????????????)
    chief_departments = db.execute('''
                                        SELECT e_id,e.name, department_name,d.department_id,description
                                        FROM employees e 
                                        INNER JOIN doctor d ON d.doc_id = e_id
                                        INNER JOIN department de ON d.department_id = de.department_id
                                        WHERE e_id IN (SELECT chief_id FROM chief)  AND d.department_id=?
                                    ''', (department_id,)).fetchone()
    # ????????????????????????????????????????????????
    candidate_chief = db.execute('''
                                            SELECT e_id,e.name
                                            FROM employees e 
                                            WHERE e_id NOT IN (SELECT chief_id FROM chief)  
                                        ''', ).fetchall()
    chiefdic = {}
    for i in candidate_chief:
        chiefdic[i[0]] = i[1]

    if request.method == "POST":
        name = request.form['dname']
        description = request.form['description']
        chief_id = request.form['chief']
        # print(name, description, chief_id)

        db.execute('''UPDATE department SET department_name = ?,description=? WHERE department_id =?''',
                   (name, description, department_id))
        log_write(user=username, action='edit', dist='department')
        db.execute('''UPDATE chief SET chief_id = ?,department_id=? WHERE department_id =?''',
                   (chief_id, department_id, department_id))
        log_write(user=username, action='edit', dist='chief')
        db.execute('''UPDATE doctor SET department_id=? WHERE doc_id =?''',
                   (department_id, chief_id))

        flash('Successfully modified information')
        return render_template('loading.html')

    return render_template('admin_update_department.html', name=username,allinf=chief_departments,chiefdic=chiefdic)


# @bp.route('/admin/?<string:username>/delete_department/<id>', methods=['GET', 'POST'])
# def delete_department(username, id):
#     department_id = id
#
#     db.execute("DELETE FROM chief WHERE department_id=?", (department_id,))
#     db.execute("DELETE FROM department WHERE department_id=?", (department_id,))
#
#     db.commit()
#     return redirect(url_for('admin.doctors',username=username))


# ????????????
# ---------------------------------------------------

@bp.route('/admin/?<string:username>/records',methods=['GET', 'POST'])
def records(username):
    # ??????????????????????????????????????????(app_id,??????????????????????????????id????????????????????????id??????????????????????????????????????????????????????)
    prescriptions_records = db.execute('''SELECT p.app_id,pat.name, e.name, p.date,med_name,med_quantity,temperature,chief_complaint,
        present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
        FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
        INNER JOIN employees e ON e.e_id = p.doc_id 
        INNER JOIN medicine m ON m.med_id = p.med_id 
        LEFT JOIN medical_record r ON p.app_id = r.app_id
        ORDER BY p.date DESC''').fetchall()
    log_write(user=username, action='visit', dist='prescription')
    log_write(user=username, action='visit', dist='records')

    predic = {}
    for cnt in prescriptions_records:
        lst = []
        for i in range(len(cnt)):
            if cnt[i] == None:
                lst.append('???')
            else:
                lst.append(cnt[i])

        predic[cnt[0]] = lst

    return render_template('admin_records.html',patients = predic,name = username,sidebarItems=adminItems,records=prescriptions_records)

@bp.route('/admin/?<string:username>/add_record',methods=['GET', 'POST'])
def add_record(username):
    # ?????????????????????????????????????????????
    app_list = db.execute('''SELECT app_id
        FROM appointment 
        WHERE app_id NOT IN (SELECT app_id FROM medical_record)
        AND date<=? ORDER BY date DESC''', (datetime.date.today(),)).fetchall()

    if len(app_list)==0:
        flash('????????????????????????')
        return redirect(url_for('admin.records', username=username))
    if request.method == "POST":
        app_id = request.form['appointment']
        appointment_inf = db.execute("SELECT  a.patient_id,a.date,a.doc_id FROM appointment a \
                                            INNER JOIN employees e ON e_id = doc_id \
                                            INNER JOIN patient p ON a.patient_id = p.patient_id \
                                            WHERE app_id=?", (app_id,)).fetchone()
        patient_id = appointment_inf[0]
        doc_id = appointment_inf[2]
        app_date = appointment_inf[1]

        temperature = request.form['temperature']
        chief_complaint = request.form['chc']
        present_illness_history = request.form['pih']
        past_history = request.form['phistory']
        allergic_history = request.form['ahistory']
        onset_date = request.form['ondate']
        current_treatment = request.form['ctreat']
        diagnosis_assessment = request.form['assess']
        med_id = request.form['medid']
        med_quantity = request.form['quantity']

        pre_id = db.execute('''INSERT INTO prescription(patient_id,doc_id,date,med_id,med_quantity,app_id)
                                   VALUES(?,?,?,?,?,?)''',
                            (patient_id, doc_id, datetime.date.today(), med_id, med_quantity, app_id)).lastrowid
        m_id = db.execute('''INSERT INTO medical_record(patient_id,doc_id,date,temperature,chief_complaint
                                    ,present_illness_history,past_history,allergic_history,onset_date,current_treatment
                                    ,diagnostic_assessment,app_id)
                                   VALUES(?,?,?,?,?,?,?,?,?,?,?,?)''',
                          (patient_id, doc_id, datetime.date.today(), temperature, chief_complaint,
                           present_illness_history, past_history, allergic_history, onset_date, current_treatment,
                           diagnosis_assessment, app_id)).lastrowid
        log_write(user=username, action='add', dist='prescription')
        log_write(user=username, action='add', dist='records')
        db.commit()
        flash('Successfully add record')
        return render_template('loading.html')
    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}

    for i in medicine_inf:
        meddic[i[0]] = i[1]


    return render_template('admin_record_add_working.html', appdic = app_list,name=username, meddic=meddic)


@bp.route('/admin/?<string:username>/update_record/<id>',methods=['GET', 'POST'])
def update_record(username, id):
    app_id = id


    # ?????????????????????????????????
    prescription_record = db.execute('''SELECT p.app_id,pat.name, e.name, p.date,med_name,med_quantity,temperature,chief_complaint,
        present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
        FROM prescription p INNER JOIN patient pat ON pat.patient_id = p.patient_id
        INNER JOIN employees e ON e.e_id = p.doc_id 
        INNER JOIN medicine m ON m.med_id = p.med_id 
        LEFT JOIN medical_record r ON p.app_id = r.app_id
        WHERE p.app_id = ?
        AND p.date<=? ORDER BY p.date DESC''', (app_id, datetime.date.today())).fetchone()
    # ??????????????????



    medicine_inf = db.execute("SELECT  * FROM medicine").fetchall()
    meddic = {}
    nowmedid = 0
    for i in medicine_inf:
        meddic[i[0]] = i[1]
        if i[1] == prescription_record[3]:
            nowmedid = i[0]

    if request.method == "POST":

        temperature = request.form['temperature']
        chief_complaint = request.form['chc']
        present_illness_history = request.form['pih']
        past_history = request.form['phistory']
        allergic_history = request.form['ahistory']
        onset_date = request.form['ondate']
        current_treatment = request.form['ctreat']
        diagnosis_assessment = request.form['assess']
        med_id = request.form['medid']
        med_quantity = request.form['quantity']

        db.execute(
            "UPDATE medical_record SET temperature=?,chief_complaint=?,present_illness_history=?,past_history=?\
            ,allergic_history=?,onset_date=?,current_treatment=?,diagnostic_assessment= ?\
             WHERE app_id=?",
            (temperature, chief_complaint, present_illness_history, past_history, allergic_history,
             onset_date, current_treatment, diagnosis_assessment, app_id))
        db.execute('''UPDATE prescription SET med_id = ?,med_quantity=?
                        WHERE app_id=?'''
                   , (med_id, med_quantity, app_id))
        log_write(user=username, action='edit', dist='prescription')
        log_write(user=username, action='edit', dist='records')
        db.commit()
        flash('Successfully modified information')
        return render_template('loading.html')

    return render_template('admin_record_update_working.html', appid = app_id,prescription_record=prescription_record, name=username,nowmedid = nowmedid,meddic = meddic)



@bp.route('/admin/?<string:username>/delete_record/<id>', methods=['GET', 'POST'])
def delete_record(username, id):
    app_id = id
    db.execute("DELETE FROM prescription WHERE app_id=?", (app_id,))
    db.execute("DELETE FROM medical_record WHERE app_id=?", (app_id,))
    log_write(user=username, action='delete', dist='prescription')
    log_write(user=username, action='delete', dist='records')
    db.commit()

    return render_template('loading.html')

@bp.route('/admin/?<string:username>/query',methods=['GET','POST'])
def query(username):
    meds = rs.MinMedIn7days()
    departs = rs.HighTempDepartIn14days()
    docs = rs.LowerAvgDocIn30days()
    missed_pats = rs.MissedAppoIn30days()
    top_doc = rs.RecPreRankTop()
    visit_pats = rs.PatRankTop()

    return render_template('admin_query.html', meds=meds, departs=departs, docs=docs, missed_pats=missed_pats,
                           top_doc=top_doc, visit_pats=visit_pats, name=username, sidebarItems=adminItems)
