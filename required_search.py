import functools
from flask import (
    Blueprint, flash, g, redirect, render_template, request, session, url_for
)
from dbfunc import connect_db,match_user_pwd,disconnect_db,get_domain,insert_user_pwd
from dbfunc import databasePATH
import time

db = connect_db(databasePATH)

def MinMedIn7days():
    # 七天内总数最少的【药品名称】
    meds = db.execute(
       "SELECT DISTINCT med_name \
        FROM prescription NATURAL JOIN medicine \
        WHERE med_quantity = (SELECT MIN(med_quantity) FROM prescription WHERE julianday('now') - julianday(date) <= 7)"
    ).fetchall()
    ret = []
    for i in meds:
        ret.append(i[0])
    ret2 = {}
    for i in ret:
        ret2[i] = i
    # print(ret2)
    return ret2

def HighTempDepartIn14days():
    # 14天内出现高温患者的【科室名称】
    departs = db.execute(
        "SELECT DISTINCT department_name\
        FROM doctor NATURAL JOIN department \
        WHERE EXISTS (SELECT * FROM medical_record WHERE temperature > 37.3 AND doctor.doc_id = medical_record.doc_id AND julianday('now') - julianday(medical_record.date) <= 14)"
    ).fetchall()
    ret = []
    for i in departs:
        ret.append(i[0])
    ret2 = {}
    for i in ret:
        ret2[i] = i
    # print(ret2)
    return ret2

def LowerAvgDocIn30days():
    # 30天接诊患者低于平均水平的【医生姓名与科室名称】
    docs = db.execute(
        "SELECT name, department_name \
        FROM employees JOIN (SELECT doc_id, department_name, COUNT(*) as rec_counts \
        FROM	(SELECT doc_id FROM medical_record WHERE julianday('now') - julianday(date) <= 30) NATURAL JOIN doctor NATURAL JOIN department \
        GROUP BY doc_id HAVING rec_counts <= (SELECT AVG(rec_counts) FROM (SELECT doc_id, COUNT(*) as rec_counts FROM (SELECT doc_id,date \
        FROM medical_record WHERE julianday('now') - julianday(date) <= 30) GROUP BY doc_id))) WHERE doc_id = e_id"
    ).fetchall()
    ret2 = {}
    for i in docs:
        ret2[i[0]] = i[1]
    # print(ret2)
    return ret2

def MissedAppoIn30days():
    # 30天内爽约超2次的【患者名称，身份证】
    pats = db.execute(
        "SELECT name, passport\
        FROM appointment NATURAL JOIN patient\
        WHERE app_id != (SELECT app_id\
                        FROM appointment NATURAL join medical_record)\
        AND julianday('now') - julianday(date) <= 30\
        GROUP BY patient_id\
        HAVING COUNT(app_id) > 2"
    ).fetchall()
    ret2 = {}
    for i in pats:
        ret2[i[0]] = i[1]
    # print(ret2)
    return ret2

def RecPreRank():
    # 病历处方排行，显示【医生名称，科室名称，病历数量，处方数量】
    rank = db.execute(
        "SELECT name, department_name, rec_counts, pre_counts\
        FROM employees JOIN (SELECT doc_id, department_name, rec_counts, pre_counts\
                            FROM  (SELECT doc_id, COUNT(*) as pre_counts\
                                        FROM prescription\
                                        GROUP BY doc_id) \
                                        NATURAL JOIN\
                                        (SELECT doc_id, COUNT(*) as rec_counts\
                                        FROM medical_record\
                                        GROUP BY doc_id)\
                                        NATURAL JOIN doctor NATURAL JOIN department\
                            ORDER BY rec_counts DESC, pre_counts DESC)\
        WHERE e_id = doc_id"
    ).fetchall()
    ret2 = {}
    for i in rank:
        ret2[i[0]] = [i[1],i[2],i[3]]
    # print(ret2)
    return ret2

def RecPreRankTop():
    # 病历处方排行第一的【医生姓名，科室名称，病历数量，处方数量】
    doc = db.execute(
        "WITH rank AS (SELECT doc_id, rec_counts, pre_counts\
							FROM  (SELECT doc_id, COUNT(*) as pre_counts\
										FROM prescription\
										GROUP BY doc_id) \
										NATURAL JOIN\
										(SELECT doc_id, COUNT(*) as rec_counts\
										FROM medical_record\
										GROUP BY doc_id)\
										NATURAL JOIN doctor\
							ORDER BY rec_counts DESC, pre_counts DESC),\
        top AS (SELECT rec_counts as top_rec, pre_counts as top_pre FROM rank LIMIT 1)\
        SELECT name, department_name, rec_counts, pre_counts\
        FROM rank NATURAL join doctor LEFT JOIN employees on e_id=doc_id NATURAL JOIN department JOIN top\
        WHERE rank.rec_counts=top_rec\
        AND rank.pre_counts=top_pre"
    ).fetchall()
    ret2 = {}
    for i in doc:
        ret2[i[0]] = [i[1],i[2],i[3]]
    # print(ret2)
    return ret2

def PatRankTop():
    # 就诊次数前十的【患者姓名，就诊次数】
    pat = db.execute(
        "SELECT name, COUNT(*) as times_visited\
        FROM medical_record NATURAL JOIN (SELECT patient_id, name FROM patient)\
        WHERE date >= '2021-01-01'\
        GROUP BY patient_id\
        ORDER BY COUNT(*) DESC, name ASC\
        LIMIT 10"
    ).fetchall()
    log_write('admin', 'visit', 'medical_record')
    log_write('admin', 'visit', 'patient')
    ret = {}
    for p in pat:
        ret[p[0]] = p[1]
    # print(ret)
    return ret

def log_write(user, action, dist):
    date = str(time.strftime("%Y-%m-%d", time.localtime()))
    log_path = 'log.txt'
    with open(log_path, 'a') as f:
        f.write(f'{date} {user} {action} {dist}\n')
        f.close()

# 仅作测试
if __name__ == "__main__":
    MinMedIn7days()
    HighTempDepartIn14days()
    RecPreRank()
    RecPreRankTop()
    PatRankTop()
    LowerAvgDocIn30days()
    # log_write('admin', 'visit', 'records')
    # log_write('admin', 'visit', 'patients')
