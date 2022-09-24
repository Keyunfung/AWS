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

@app.route("/payroll/generatepayroll", methods=['GET','POST'])
def payrollgeneratepayroll():
    return render_template('calculate-payroll.html')

@app.route("/payroll/update", methods=['GET','POST'])
def payrollupdate():
    return render_template('update-payroll.html')

@app.route("/payroll/update/info", methods=['GET','POST'])
def payrollupdateinfo():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        
        try:
            payroll_month = dt.datetime.strptime(request.form['payroll_month'],'%Y-%m').strftime(format="%B %Y")
        except Exception as e:
            errorMessage = "Please fill in month and year for payroll"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        if emp_id == "":
            errorMessage = "Please fill in Employee ID"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        cursor = db_conn.cursor()
        select_sql = "SELECT * FROM payroll where emp_id = (%s) and payroll_month = (%s)"
        try:
            cursor.execute(select_sql, (emp_id, payroll_month))
            if cursor.rowcount == 0:
                errorMessage = "The payroll for " + emp_id + " does not exist in " + payroll_month
                action = "/payroll/update"
                return render_template('error-message.html', errorMsg = errorMessage, action = action)
        finally:
            cursor.close()

        return render_template('update-salary-payroll.html', emp_id = emp_id, payroll_month = payroll_month)
    else:
        emp_id = request.args.get('emp_id')
        payroll_month = request.args.get('payroll_month')
        return render_template('update-salary-payroll.html', emp_id = emp_id, payroll_month = payroll_month)

@app.route("/payroll/update/info/updatepayroll", methods=['GET','POST'])
def payrollupdateinfoupdatepayroll():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        payroll_month = request.form['payroll_month']
        
        try:
            workday = float(request.form['work_day'])
        except Exception as e:
            errorMessage = "Invalid input for working day per week"
            action = "/payroll/update/info/updatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hourrate = float(request.form['hour_rate'])
        except Exception as e:
            errorMessage = "Invalid input for hourly rate"
            action = "/payroll/update/info/updatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hourwork = float(request.form['hour_work'])
        except Exception as e:
            errorMessage = "Invalid input for hours work"
            action = "/payroll/update/info/updatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        monthly_salary = workday * hourwork * hourrate
        
        cursor = db_conn.cursor()
        select_sql = "SELECT * FROM payroll where emp_id = (%s) and payroll_month = (%s)"
        cursor.execute(select_sql, (emp_id, payroll_month))
        data = cursor.fetchall()
        print("work day")
        print(data.emp_id)
        print(data.work_day)
        print("hour rate")
        print(db_hour_rate)
        print("hour work")
        print(db_hour_work)
        if workday == select_sql[0] and hourrate == select_sql[1] and hourwork == select_sql[2]:
            errorMessage = "The payroll is same in the database"
            action = "/payroll/update/info/updatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        try:   
            update_payroll = "update payroll set monthly_salary = %s, work_day = %s, hour_rate = %s, hour_work = %s where emp_id = %s and payroll_month = %s"
            cursor.execute(update_payroll, (monthly_salary, work_day, hour_rate, hour_work, emp_id, payroll_month))
        finally:
            db_conn.commit()
            cursor.close()

        return render_template('payroll-output.html', title = 'Payroll updated successfully', emp_id = emp_id, payroll_month = payroll_month, monthly_salary = monthly_salary)
    else:
        emp_id = request.args.get('emp_id')
        payroll_month = request.args.get('payroll_month')
        work_day = request.args.get('work_day')
        hour_rate = request.args.get('hour_rate')
        hour_work = request.args.get('hour_work')
        return render_template('payroll-output.html', title = 'Payroll updated successfully', emp_id = emp_id, payroll_month = payroll_month, monthly_salary = monthly_salary)

@app.route("/payroll/generatepayroll/results", methods=['GET','POST'])
def generatepayrollresult():
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
            
        return render_template('payroll-output.html', title = 'New Payroll added successfully', emp_id = emp_id, payroll_month = payroll_month, monthly_salary = monthly_salary)
    else:
        emp_id = request.args.get('emp_id')
        work_day = request.args.get('work_day')
        hour_rate = request.args.get('hour_rate')
        hour_work = request.args.get('hour_work')
        payroll_month = request.args.get('payroll_month')
        return render_template('payroll-output.html')

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=80, debug=True)
