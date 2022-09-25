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
table = 'leave'

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about/", methods=['GET','POST'])
def about():
    return render_template('about.html')

@app.route("/employee/", methods=['GET','POST'])
def employee():
    return render_template('employee.html')

@app.route("/attendance/", methods=['GET','POST'])
def attendance():
    return render_template('attendance.html')

@app.route("/leave/", methods=['GET','POST'])
def leave():
    return render_template('leave.html')

@app.route("/leave/output", methods=['GET','POST'])
def leaveoutput():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        startdate = dt.datetime.strptime(request.form['startdate'], '%Y-%m-%d').strftime(format="%d-%b-%Y")
        enddate = dt.datetime.strptime(request.form['enddate'], '%Y-%m-%d').strftime(format="%d-%b-%Y")
        description = request.form['description']
#         status = "Pending"
#         statusdate = dt.datetime.now().strftime(format="%d-%b-%Y")
#         statustime = dt.datetime.now().strftime(format="%H:%M:%S")
        insert_sql = "INSERT INTO leavetest VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()
        try:
            cursor.execute(insert_sql, (emp_id, startdate, enddate, description))
            db_conn.commit()
        finally:
            cursor.close()
            
        return render_template('payroll-output.html', title = 'Employee Leave Added Successfully', emp_id = emp_id)
    else:
        emp_id = request.form['emp_id']
        startdate = request.form['startdate']
        enddate = request.form['enddate']
        description = request.form['description']
#         status = " "
#         statusdate = dt.datetime.now().strftime(format="%d-%b-%Y")
#         statustime = dt.datetime.now().strftime(format="%H:%M:%S")
        
        return render_template('leave-output.html', title = 'Employee Leave Added Unsuccessfully')

@app.route("/leave/statusupdate", methods=['GET','POST'])
def leavestatus():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        status = request.form['status']
        statusdate = dt.datetime.now().strftime(format="%d-%b-%Y")
        statustime = dt.datetime.now().strftime(format="%H:%M:%S")
        
        cursor = db_conn.cursor()
        update_sql = "UPDATE leave SET status = (%(status)s) AND statusdate = (%(statusdate)s) AND statustime = (%(statustime)s) WHERE emp_id = (%(emp_id)s)"
        try:
            cursor.execute(select_sql, (emp_id, status, statusdate, statustime))
            db_conn.commit()
        finally:
            cursor.close()
            
        return render_template('leave.html')
    else:
        emp_id = request.form['emp_id']
        status = request.form['status']
        
        return render_template('leave.html')


################### PAYROLL #################################
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
        
        if emp_id == "":
            errorMessage = "Please fill in Employee ID"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            payroll_month = dt.datetime.strptime(request.form['payroll_month'],'%Y-%m').strftime(format="%B %Y")
        except Exception as e:
            errorMessage = "Please fill in month and year for payroll"
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
            work_day = int(request.form['work_day'])
        except Exception as e:
            errorMessage = "Invalid input for working day per week"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hour_rate = float(request.form['hour_rate'])
        except Exception as e:
            errorMessage = "Invalid input for hourly rate"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hour_work = float(request.form['hour_work'])
        except Exception as e:
            errorMessage = "Invalid input for hours work"
            action = "/payroll/update"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        monthly_salary = work_day * hour_work * hour_rate
        
        cursor = db_conn.cursor()
        select_sql = "SELECT * FROM payroll where emp_id = (%s) and payroll_month = (%s) and hour_rate = (%s) and hour_work = (%s) and work_day = (%s)"
        cursor.execute(select_sql, (emp_id, payroll_month, hour_rate, hour_work, work_day))
        if cursor.rowcount != 0:
            errorMessage = "The updated payroll is same in the database"
            action = "/payroll/update"
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
        
        if emp_id == "":
            errorMessage = "Please fill in Employee ID"
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            work_day = int(request.form['work_day'])
        except Exception as e:
            errorMessage = "Invalid input for working day per week"
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hour_rate = float(request.form['hour_rate'])
        except Exception as e:
            errorMessage = "Invalid input for hourly rate"
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            hour_work = float(request.form['hour_work'])
        except Exception as e:
            errorMessage = "Invalid input for hours work"
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
        
        try:
            payroll_month = dt.datetime.strptime(request.form['payroll_month'],'%Y-%m').strftime(format="%B %Y")
        except Exception as e:
            errorMessage = "Please fill in month and year for payroll"
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
                
        monthly_salary = work_day * hour_work * hour_rate
        
        insert_sql = "INSERT INTO payroll VALUES (%s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()
        
        select_sql = "SELECT * FROM payroll where emp_id = (%s) and payroll_month = (%s)"
        cursor.execute(select_sql, (emp_id, payroll_month))
        if cursor.rowcount != 0:
            errorMessage = "The payroll for " + emp_id + " exists in " + payroll_month + "."
            action = "/payroll/generatepayroll"
            return render_template('error-message.html', errorMsg = errorMessage, action = action)
            
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
