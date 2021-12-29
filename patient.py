import functools
import sqlite3
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
from sliderbaritem import patientItems
bp = Blueprint('patient', __name__)

db = connect_db(databasePATH)

def get_id(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/patient/?<string:username>',methods=['GET','POST'])
def patient(username):
    if session.get(username) is not None:
        patient = db.execute("SELECT * FROM patient WHERE username=?", (username,)).fetchall()
        return render_template('patient.html',name = username,sidebarItems=patientItems, patient=patient)
    return redirect(url_for('auth.login'))

@bp.route('/patient/?<string:username>/departments')
def departments(username):
    departments = db.execute("SELECT * FROM department").fetchall()
    dicdep = {}
    for cnt in range(len(departments)):
        i,j = departments[cnt][0],departments[cnt][1]
        dicdep[i] = j
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

    return render_template('patient2departments.html', name = username,sidebarItems=patientItems,alldepartments = dicdep,dfd = dfddic,docdic = docdic)

@bp.route('/patient/?<string:username>/change_inf/',methods=['GET','POST'])
def change_inf(username):
    if request.method == "POST":
        name = request.form['name']
        DOB = request.form['DOB']
        passport = request.form['passport']
        uuser = request.form['username']
        gender = request.form['gender']
        phone = request.form['phone']
        email = request.form['email']
        pwd = request.form['pwd']
        repwd = request.form['repwd']

        if pwd == "NULL" and pwd == repwd:
            #判断pwd有没有修改，因为不会在界面show给用户，null为用户没有输入即没有修改
            #还要判断username修改后在数据库是不是唯一，我记得dbfunc有写过你看一下跟register差不多
            #有错就redirect到这个页面并且flash一个信息
            pass
        else:
            pass

        #写一个修改个人资料到db

        return redirect(url_for('patient.patient', username=username))


    allinf = db.execute('''
                                SELECT patient_id,name,DOB,passport,gender,phone,email,username
                                FROM patient
                                WHERE username =?   
                            ''',(username,)).fetchall()

    #print(allinf[0])
    i, j, k, l, m, n, o,p = allinf[0][0], allinf[0][1], allinf[0][2], allinf[0][3], allinf[0][4], allinf[0][5],allinf[0][6],allinf[0][7]

    infdic = [j, k, l, m, n, o,p]
    #print(infdic)
    return render_template('patient_change_inf.html', name = username,sidebarItems = patientItems,allinf = infdic)


@bp.route('/patient/?<string:username>/department/<id>')
def department(username,id):
    department = db.execute('SELECT * FROM department WHERE department_id=?', (id,)).fetchall()
    return render_template('patient_department.html', department=department)

@bp.route('/patient/?<string:username>/doctors')
def doctors(username):
    doctors = db.execute("SELECT * FROM employees").fetchall()
    return render_template('patient_doctors.html', doctors=doctors)

@bp.route('/patient/?<string:username>/doctor/<id>')
def doctor(username, id):
    doctor = db.execute('SELECT * FROM employees WHERE e_id=?', (id,)).fetchall()
    return render_template('patient_doctor.html', doctor=doctor)


