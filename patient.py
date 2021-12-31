import datetime
import functools
import sqlite3
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH,check_repeat,log_write
from sliderbaritem import patientItems
bp = Blueprint('patient', __name__)

db = connect_db(databasePATH)

def get_name(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from patient \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/patient/?<string:username>',methods=['GET','POST'])
def patient(username):
    realname = get_name(db, username)
    if session.get(username) is not None:
        patient = db.execute("SELECT * FROM patient WHERE username=?", (username,)).fetchall()
        log_write(user=username, action='visit', dist='patient')
        return render_template('patient.html',realname = realname,name = username,sidebarItems=patientItems, patient=patient)
    return redirect(url_for('auth.login'))

@bp.route('/patient/?<string:username>/departments')
def departments(username):
    realname = get_name(db, username)
    departments = db.execute("SELECT * FROM department").fetchall()
    log_write(user=username, action='visit', dist='department')
    log_write(user=username, action='visit', dist='employees')
    dicdep = {}
    for cnt in range(len(departments)):
        i,j,k = departments[cnt][0],departments[cnt][1],departments[cnt][2]
        dicdep[i] = [j,k]
    #print(dicdep)

    doctorfromdepartments = db.execute('''
                                            SELECT doc_id,d.department_id
                                            FROM doctor d INNER JOIN department e ON d.department_id == e.department_id 
                                        ''').fetchall()
    dfddic={}
    for cnt in range(len(doctorfromdepartments)):
        i,j = doctorfromdepartments[cnt][0],doctorfromdepartments[cnt][1]
        if dfddic.get(j) == None:
            dfddic[j] = [i]
        else:
            dfddic[j].append(i)

    alldoc = db.execute('''
                            SELECT e_id,name,phone,email,graduate_school,degree,technical_title,specialty
                            FROM employees
                        ''').fetchall()

    docdic = {}
    for cnt in range(len(alldoc)):
        i, j,k,l,m,n,o,p = alldoc[cnt][0], alldoc[cnt][1],alldoc[cnt][2],alldoc[cnt][3],alldoc[cnt][4],alldoc[cnt][5],alldoc[cnt][6],alldoc[cnt][7]
        if docdic.get(i) == None:
            docdic[i] = [j,k,l,m,n,o,p]

    return render_template('patient2departments.html',realname = realname, name = username,sidebarItems=patientItems,alldepartments = dicdep,dfd = dfddic,docdic = docdic)

@bp.route('/patient/?<string:username>/change_inf/',methods=['GET','POST'])
def change_inf(username):
    realname = get_name(db, username)
    patient_id = get_id(db,username)
    if request.method == "POST":
        DOB = request.form['DOB']
        user = request.form['username']
        phone = request.form['phone']
        email = request.form['email']
        pwd = request.form['pwd']
        repwd = request.form['repwd']
        if pwd != repwd:
            flash('password is not equal to confirm_password!')
            return redirect(url_for('patient.change_inf', username=username))
        if check_repeat(db, user) and user != username:
            flash('The username already exists')
            return redirect(url_for('patient.change_inf', username=username))
        if pwd != "NULL":
            db.execute('''UPDATE login_inf 
            SET username = ?, password=?
            WHERE username = ?''', (user, pwd, username))
            db.execute(
                "UPDATE patient SET DOB=?,phone=?,email=?,username=?,password=? WHERE patient_id=?",
                (DOB, phone, email, user, pwd, patient_id))
            db.commit()
        else:
            db.execute('''UPDATE login_inf 
                        SET username = ?
                        WHERE username = ?''', (user, username))
            db.execute(
                "UPDATE patient SET DOB=?,phone=?,email=?,username=? WHERE patient_id=?",
                (DOB, phone, email, user, patient_id))
            db.commit()
        log_write(user=username, action='edit', dist='patient')
        flash('Successfully modified information')
        return redirect(url_for('patient.patient', username=user))


    allinf = db.execute('''
                                SELECT patient_id,name,DOB,passport,gender,phone,email,username
                                FROM patient
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7]

    infdic = [j, k, l, m, n, o,p]
    #print(infdic)
    return render_template('patient_change_inf.html', realname = realname,name = username,sidebarItems = patientItems,allinf = infdic)

@bp.route('/patient/?<string:username>/history',methods=['GET','POST'])
def history(username):
    patient_id = get_id(db, username)
    realname = get_name(db, username)
    # 格式为(id,医生姓名，日期，药品名字，药品用量,体温，主诉，现病史，既往史，过敏史，发病时间，治疗情况，评估诊断)
    prescriptions_records = db.execute('''SELECT e.e_id,e.name,p.date,med_name,med_quantity,temperature,chief_complaint,
    present_illness_history,past_history, allergic_history, onset_date,current_treatment, diagnostic_assessment
    FROM prescription p INNER JOIN employees e ON e.e_id = p.doc_id
    INNER JOIN medicine m ON m.med_id = p.med_id 
    LEFT JOIN medical_record r ON p.app_id = r.app_id
    WHERE p.patient_id=? AND p.date<=? ORDER BY p.date DESC''', (patient_id, datetime.date.today())).fetchall()
    log_write(user=username, action='visit', dist='prescription')
    log_write(user=username, action='visit', dist='records')
    recordsfordoc = {}
    for cnt in range(len(prescriptions_records)):
        i1,i2,i3,i4,i5,i6,i7,i8,i9,i10,i11,i12,i13 = prescriptions_records[cnt][0],prescriptions_records[cnt][1],prescriptions_records[cnt][2],prescriptions_records[cnt][3], \
                                                     prescriptions_records[cnt][4],prescriptions_records[cnt][5],prescriptions_records[cnt][6],prescriptions_records[cnt][7], \
                                                     prescriptions_records[cnt][8],prescriptions_records[cnt][9],prescriptions_records[cnt][10],prescriptions_records[cnt][11], \
                                                     prescriptions_records[cnt][12]
        if recordsfordoc.get(i1) == None:
            recordsfordoc[i1] = [[i2,i3,i4,i5,i6,i7,i8,i9,i10,i11,i12,i13]]
        else:
            recordsfordoc[i1].append([i2,i3,i4,i5,i6,i7,i8,i9,i10,i11,i12,i13])

    #print(recordsfordoc)

    records = {}
    for cnt in range(len(prescriptions_records)):
        i1, i2, i3, i4, i5, i6, i7, i8, i9, i10, i11, i12, i13 = prescriptions_records[cnt][0], \
                                                                 prescriptions_records[cnt][1], \
                                                                 prescriptions_records[cnt][2], \
                                                                 prescriptions_records[cnt][3], \
                                                                 prescriptions_records[cnt][4], \
                                                                 prescriptions_records[cnt][5], \
                                                                 prescriptions_records[cnt][6], \
                                                                 prescriptions_records[cnt][7], \
                                                                 prescriptions_records[cnt][8], \
                                                                 prescriptions_records[cnt][9], \
                                                                 prescriptions_records[cnt][10], \
                                                                 prescriptions_records[cnt][11], \
                                                                 prescriptions_records[cnt][12]
        if records.get(cnt) == None:
            cntt = countfunc(records,i1)
            records[cnt] = [i1,i2,i3,i4,i5,i6,i7,i8,i9,i10,i11,i12,i13,cntt]

    #print(records)
    alldoctor = db.execute('''
                                    SELECT department_name,e_id
                                    FROM appointment a 
                                    INNER JOIN employees e ON e_id = doc_id
                                    INNER JOIN department m ON a.department_id = m.department_id
                                ''').fetchall()
    dicdoctor = {}

    for cnt in range(len(alldoctor)):
        i, j = alldoctor[cnt][0], alldoctor[cnt][1]
        if dicdoctor.get(j) == None:
            dicdoctor[j] = i

    return render_template('patient_history.html',realname = realname,name = username,sidebarItems = patientItems,alldoc = dicdoctor,records = records,rfordoc = recordsfordoc,hav = len(records))
# 待写前端
# ---------------------------------------------------

@bp.route('/patient/?<string:username>/bill',methods=['GET','POST'])
def bill(username):
    patient_id = get_id(db, username)
    realname = get_name(db, username)
    # 格式为(价格,日期,医生,科室,药名,单价)
    bills = db.execute('''SELECT bill_id, cost, p.date, e.name, department_name, p.med_name, med_price
    FROM bill b INNER JOIN appointment a ON b.app_id = a.app_id
    INNER JOIN prescription p ON p.app_id = b.app_id
    INNER JOIN employees e ON e.e_id = a.doc_id
    INNER JOIN employees medicine m ON m.med_id = p.med_id  
    WHERE b.patient_id=? ORDER BY p.date DESC''', (patient_id, )).fetchall()
    log_write(user=username, action='visit', dist='bill')
    billdic = {}


    return render_template('patient_bill.html',realname = realname,name = username,sidebarItems = patientItems,hav = len(bills),billdic=billdic)

@bp.route('/patient/?<string:username>/pay/<id>',methods=['GET','POST'])
def pay(username, id):
    patient_id = get_id(db, username)
    realname = get_name(db, username)
    # 格式为(价格,日期,医生,科室,药名,单价)
    bill_id = id
    db.execute('''DELETE FROM bill WHERE bill_id=?''',(bill_id))
    db.commit()
    log_write(user=username, action='delete', dist='bill')
    return render_template('loading.html')

def countfunc(dicc,iid):
    count = 0

    for i in dicc:
        if dicc[i][0] == iid:
            count = count + 1
    return count




