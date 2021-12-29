import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd,get_id
from dbfunc import databasePATH
from sliderbaritem import patientItems,doctorItems
bp = Blueprint('appointment', __name__)

db = connect_db(databasePATH)
APP_NUM = 20

def get_pname(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from patient \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_ename(db,user):
    cur = db.cursor()
    tt = cur.execute("select name \
                          from employees \
                          where username = '%s'" % user)
    for i in tt:
        return i[0]

def get_eid(db,user):
    cur = db.cursor()
    tt = cur.execute("select e_id \
                      from employees \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

def get_pid(db,user):
    cur = db.cursor()
    tt = cur.execute("select patient_id \
                      from patient \
                      where username = '%s'" %user)
    for i in tt:
        return i[0]

@bp.route('/doctor/?<string:username>/doctor_appointments',methods=['GET', 'POST'])
def doctor_appointments(username):
    doc_id = get_eid(db,username)
    realname = get_ename(db,username)
    appointments = db.execute("SELECT date , p.name, p.phone FROM appointment a \
                                INNER JOIN employees e ON e_id = doc_id \
                                INNER JOIN patient p ON a.patient_id = p.patient_id \
                                WHERE e_id=? ORDER BY date DESC", (doc_id,)).fetchall()

    return render_template('doctor_appointments.html',realname = realname,name = username,sidebarItems=doctorItems,appointments=appointments,hav = len(appointments))

@bp.route('/patient/?<string:username>/patient_appointments',methods=['GET','POST'])
def patient_appointments(username):
    patient_id = get_pid(db,username)
    realname = get_pname(db, username)
    appointments = db.execute(
        "SELECT date, department_name, name\
        FROM appointment a LEFT JOIN employees e ON e_id = doc_id \
        LEFT JOIN department d ON d.department_id = a.department_id \
        WHERE patient_id=? ORDER BY date DESC", (patient_id,)
    ).fetchall()
    #print(patient_id)
    #print(appointments)
    return render_template('patient_appointments.html', realname = realname,name = username,sidebarItems=patientItems,appointments=appointments,hav = len(appointments))

@bp.route('/patient/?<string:username>/add_appointment',methods=['GET','POST'])
def patient_add_appointment(username):
    patient_id = get_pid(db,username)
    realname = get_pname(db, username)
    if request.method == 'POST':
        """api to add the appointment in the database"""
        patient_id = get_id(db,username)

        app_date = request.form['date']
        department_name = request.form['de_id']
        doc_name = request.form['doc_id']

        survey = None
        error = None

        temperature = request.form['temperature']
        province = '北京'#未完成 先设为这个
        city = '市辖区' #未完成 先设为这个
        district = '海淀区' #未完成 先设为这个
        symptom = request.form['rm']#返回为有症状或无症状
        risk = request.form['r14']#返回为曾到或未曾到

        '''# 暂时定为bool值
        is_visit = request.form['visit']
        if is_visit == True:
            is_visit_str = '是'
        else:
            is_visit_str = '否'
        '''
        address = f'省：{province}；\n城市：{city}；\n区：{district}；'

        #app_id = db.execute('''INSERT INTO appointment(date,patient_id,department_id,doc_id,temperature,address,symptom,risk)
        #                    VALUES(?,?,?,?,?,?,?,?)''',
        #                    (app_date, patient_id, department_id, doc_id, temperature,address,symptom,risk)).lastrowid
        #db.commit()
        #先不提交
        
        

        return redirect(url_for('appointment.patient_appointments',username = username))


    name_and_passport_phone = db.execute('''
                                    SELECT name,passport,phone
                                    FROM patient
                                    where username=?
                                ''',(username,)).fetchall()
    npldic = {'name':name_and_passport_phone[0][0],'passport':name_and_passport_phone[0][1],'phone':name_and_passport_phone[0][2]}
    alldepartments = db.execute('''
                                    SELECT department_name,department_id
                                    FROM department
                                ''').fetchall()
    dicdep = {}
    for cnt in range(len(alldepartments)):
        i,j = alldepartments[cnt][0],alldepartments[cnt][1]
        if dicdep.get(i) == None:
            dicdep[i] = j

    alldoctor = db.execute('''
                                SELECT name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                            ''').fetchall()
    dicdoctor={}

    for cnt in range(len(alldoctor)):
        tempjudge = False
        i,j,k = alldoctor[cnt][0],alldoctor[cnt][1],alldoctor[cnt][2]
        if dicdoctor.get(j) == None:
            dicdoctor[j] = [[k,i]]
        else:
            for z in dicdoctor[j]:
                if z[0] == k:
                    tempjudge = True
            if tempjudge == False:
                dicdoctor[j].append([k,i])


    appointments = db.execute('''
                                SELECT date,name,department_name,e_id
                                FROM appointment a 
                                INNER JOIN employees e ON e_id = doc_id
                                INNER JOIN department m ON a.department_id = m.department_id
                            ''').fetchall()
    #print(appointments)
    dic={}
    for cnt in range(len(appointments)):
        i,j,k,l = appointments[cnt][0],appointments[cnt][1],appointments[cnt][2],appointments[cnt][3]
        #print(i,j,k)
        if dic.get(i+','+k) == None:
            dic[i+','+k] = [[j,1,l]]
        else:
            for z in dic[i+','+k]:
                if z[2] == l:
                    z[1] = z[1] + 1
            if z[2] != l:
                dic[i+','+k].append([j,1,l])

    #print(dicdoctor)
    #print(dic)
    #print(npldic)
    return render_template('patient_add_appointment.html', realname = realname,name = username,sidebarItems = patientItems,appointments = dic,sum = APP_NUM,alldepartments = dicdep,alldoctor = dicdoctor,npldic = npldic)







