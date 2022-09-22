from tokenize import Double
from flask import Flask, render_template, request
from pymysql import connections
import os
import boto3
from config import *
import datetime as dt

app=Flask(__name__,template_folder='template')

bucket = custombucket
region = customregion

db_conn = connections.Connection(
    host=customhost,
    port=3306,
    user=customuser,
    password=custompass,
    db=customdb

)
output = {}
table = 'employee'

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/payroll/", methods=['GET','POST'])
def payroll():
    return render_template('payroll.html')

@app.route("/payroll/addsalary", methods=['GET','POST'])
def addsalary():
    return render_template('calculate-payroll.html')

@app.route("/payroll/updatesalary", methods=['GET','POST'])
def updatesalary():
    return render_template('update-payroll.html')

@app.route("/payroll/updatesalary/info", methods=['GET','POST'])
def updatesalaryinfo():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        payroll_month = dt.datetime.strptime(request.form['payroll_month'],'%Y-%m').strftime(format="%B %Y")
        
        cursor = db_conn.cursor()
        select_sql = "SELECT * FROM payroll where emp_id = (%s) and payroll_month = (%s)"
        try:
            cursor.execute(select_sql, (emp_id, payroll_month))
        finally:
            cursor.close()

        return render_template('update-salary-payroll.html')
    else:
        emp_id = request.args.get('emp_id')
        payroll_month = request.args.get('payroll_month')
        return render_template('update-salary-payroll.html')

@app.route("/payroll/addsalary/results", methods=['GET','POST'])
def salaryresult():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        work_day = float(request.form['work_day'])
        hour_rate = float(request.form['hour_rate'])  
        hour_work = float(request.form['hour_work'])
        payroll_month = dt.datetime.strptime(request.form['payroll_month'],'%Y-%m').strftime(format="%B %Y")
        monthly_salary = work_day * hour_work * hour_rate
        insert_sql = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()
        try:
            cursor.execute(insert_sql, (emp_id, work_day, hour_rate, hour_work, payroll_month, monthly_salary))
            db_conn.commit()
        finally:
            cursor.close()

        print("all modification done...")
        return render_template('payroll-output.html', title = 'New Payroll added successfully', emp_id = emp_id,
        payroll_month = payroll_month, monthly_salary = monthly_salary)
    else:
        emp_id = request.args.get('emp_id')
        work_day = request.args.get('work_day')
        hour_rate = request.args.get('hour_rate')
        hour_work = request.args.get('hour_work')
        payroll_month = request.args.get('payroll_month')
        return render_template('payroll-output.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
