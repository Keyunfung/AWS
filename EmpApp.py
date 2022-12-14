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
table = 'attendance'

@app.route("/")
def home():
    return render_template('home.html')

@app.route("/about/", methods=['GET','POST'])
def about():
    return render_template('about.html')

################### EMPLOYEE #################################
@app.route("/employee/", methods=['GET','POST'])
def employee():
    return render_template('employee-main.html')

@app.route("/employee/add", methods=['GET','POST'])
def employeeadd():
    return render_template('employee.html')

@app.route("/employee/edit", methods=['GET','POST'])
def employeeedit():
    return render_template('update-employee.html')

@app.route("/employee/delete", methods=['GET', 'POST'])
def employeedelete():
    return render_template('delete-employee.html')

@app.route("/employee/delete/output", methods=['GET', 'POST'])
def employeedeleteoutput():

    emp_id = request.form['emp_id']

    delete_statement = "delete from employee where emp_id = %s"
    cursor = db_conn.cursor()
    cursor.execute(delete_statement, (emp_id))
    cursor.close()

    db_conn.commit()

    #Delete S3 picture
    emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
    s3_client = boto3.client('s3')

    try:
        s3_client.delete_object(Bucket=custombucket, Key=emp_image_file_name_in_s3)
        return render_template("employeedelete.html", emp_id = emp_id)

    except Exception as e:
        return str(e)

@app.route("/employee/edit/output", methods=['GET','POST'])
def employeeeditoutput():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        emp_name = request.form['emp_name']
        emp_address = request.form['emp_address']
        emp_email = request.form['emp_email']
        emp_position = request.form['emp_position']
        emp_salary = float(request.form['emp_salary'])

        cursor = db_conn.cursor()
        update_emp = "update employee set emp_id = %s, emp_name = %s, emp_address = %s, emp_email = %s, emp_position = %s, emp_salary = %s where emp_id = %s"
        cursor.execute(update_emp, (emp_id, emp_name, emp_address, emp_email, emp_position, emp_salary, emp_id))
        db_conn.commit()
        return render_template('employee-output.html', employee_output_title="Employee Updated Successfully", emp_id=emp_id, emp_name=emp_name, emp_address=emp_address, emp_salary=emp_salary, emp_email=emp_email, emp_position=emp_position)

    else:        
        emp_id = request.args.get('emp_id')
        emp_name = request.args.get('emp_name')
        emp_address = request.args.get('emp_address')
        emp_email = request.args.get('emp_email')
        emp_position = request.args.get('emp_position')
        emp_salary = request.args.get('emp_salary')
        return render_template('employee-output.html', employee_output_title="Employee Updated Successfully", emp_id=emp_id, emp_name=emp_name, emp_address=emp_address, emp_salary=emp_salary, emp_email=emp_email, emp_position=emp_position)

@app.route("/employee/output", methods=['GET','POST'])
def employeeoutput():
    if request.method == 'POST':
        emp_id = request.form['emp_id']
        emp_name = request.form['emp_name']
        emp_address = request.form['emp_address']
        emp_email = request.form['emp_email']
        emp_position = request.form['emp_position']
        emp_salary = float(request.form['emp_salary'])
        emp_img = request.files['emp_img']

        insert_sql = "INSERT INTO employee VALUES (%s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if emp_img.filename == "":
            return "Please select a file"

        try:

            cursor.execute(insert_sql, (emp_id, emp_name, emp_address, emp_email, emp_position, emp_salary))
            db_conn.commit()
            # Uplaod image file in S3 #
            emp_image_file_name_in_s3 = "emp-id-" + str(emp_id) + "_image_file"
            s3 = boto3.resource('s3')

            try:
                print("Data inserted in MySQL RDS... uploading image to S3...")
                s3.Bucket(custombucket).put_object(Key=emp_image_file_name_in_s3, Body=emp_img)
                bucket_location = boto3.client('s3').get_bucket_location(Bucket=custombucket)
                s3_location = (bucket_location['LocationConstraint'])

                if s3_location is None:
                    s3_location = ''
                else:
                    s3_location = '-' + s3_location

                object_url = "https://s3{0}.amazonaws.com/{1}/{2}".format(
                    s3_location,
                    custombucket,
                    emp_image_file_name_in_s3)

            except Exception as e:
                return str(e)

        finally:
            cursor.close()

        return render_template('employee-output.html', employee_output_title="New Employee Added Successfully", emp_id=emp_id, emp_name=emp_name, emp_address=emp_address, emp_salary=emp_salary, emp_email=emp_email, emp_position=emp_position)

    else:        
        emp_id = request.args.get('emp_id')
        emp_name = request.args.get('emp_name')
        emp_address = request.args.get('emp_address')
        emp_email = request.args.get('emp_email')
        emp_position = request.args.get('emp_position')
        emp_salary = request.args.get('emp_salary')
        emp_img = request.args.get('emp_img')
        return render_template('employee-output.html', emp_id=emp_id, emp_name=emp_name, emp_address=emp_address, emp_salary=emp_salary, emp_email=emp_email, emp_position=emp_position)

################### ATTENDANCE #################################
@app.route("/attendance/", methods=['GET','POST'])
def attendance():
    return render_template('attendance.html')

#Insert and output 1 Attendance
@app.route("/attendance/output", methods=['GET','POST'])
def attendance_input():
    # if request.method == 'POST': 
        #show to output from db
        emp_id = request.form['emp_id']
        date = request.form['date']
        time = request.form['time']
        status = request.form['status']

        #insert
        insert_sql = "INSERT INTO attendance VALUES (%s, %s, %s, %s)"
        cursor = db_conn.cursor()

        if emp_id =='' or date =='' or time =='' or status =='':
            errorMsg = "Please fill in all the fields"
            buttonMsg = "Fields is NULL"
            action = "/attendance/"
            return render_template('error-message.html',errorMsg=errorMsg,buttonMsg=buttonMsg,action=action)

        
        try:
             cursor.execute(insert_sql, (emp_id, date, time, status))
             db_conn.commit()
        except Exception as e:
            return str(e)

        finally:
            cursor.close()

        print("all modification done...")
        return render_template('attendance-output.html', emp_id=emp_id, date=date, time=time, status=status)


@app.route("/attendance/view", methods=['GET','POST'])
def attendance_viewAll():

    # emp_id = request.form['emp_id']
    # if request.method == 'POST':
        cur = db_conn.cursor()
        select_attendance_sql = "SELECT * FROM attendance"
        
        try:
            cur.execute(select_attendance_sql)

            attendance_view = []

            while True:
                attendance_view_data = cur.fetchone()
                if attendance_view_data is None:
                    break
                    # errorMsg = "The data no exist"
                    # buttonMsg = "Fields is NULL"
                    # action = "/attendance/"
                    # return render_template ('error-message.html',errorMsg=errorMsg,buttonMsg=buttonMsg,action=action)
                
                else:
                    attendance_view.append(attendance_view_data)

        except Exception as e:
            return str(e)
        
        finally:
            cur.close()

        return render_template('attendance-view.html',attendance_view=attendance_view)

################### LEAVE #################################
@app.route("/leave/", methods=['GET','POST'])
def leave():
    return render_template('leave.html')

@app.route("/leave/output", methods=['GET','POST'])
def leaveoutput():
    if request.method == 'POST':
        leave_emp_id = request.form['leave_emp_id']
        dtstartdate = request.form['leave_startdate']
        dtenddate = request.form['leave_enddate']
        leave_startdate = dt.datetime.strptime(dtstartdate, "%Y-%m-%d").strftime(format="%d-%b-%Y")
        leave_enddate = dt.datetime.strptime(dtenddate, "%Y-%m-%d").strftime(format="%d-%b-%Y")
        leave_description = request.form['leave_description']
        leave_status = "Pending"
        leave_statusdate = dt.datetime.now().strftime(format="%d-%b-%Y")
        leave_statustime = dt.datetime.now().strftime(format="%H:%M:%S")
        insert_leave_sql = "INSERT INTO leavetest VALUES (%s, %s, %s, %s, %s, %s, %s)"
        cursor = db_conn.cursor()
        
        select_leave_sql = "SELECT * FROM leavetest WHERE leave_emp_id=(%s) and leave_startdate=(%s) and leave_enddate=(%s) and leave_description=(%s) and leave_status=(%s)"
        try:
            cursor.execute(insert_leave_sql, (leave_emp_id, leave_startdate, leave_enddate, leave_description, leave_status, leave_statusdate, leave_statustime))
            db_conn.commit()
        finally:
            cursor.close()
            
        return render_template('leave-output.html', leave_output_title = 'Employee Leave Added Successfully', emp_id=leave_emp_id, leave_emp_id=leave_emp_id, leave_startdate=leave_startdate, leave_enddate=leave_enddate, leave_description=leave_description, leave_status=leave_status)
    else:
        leave_emp_id = request.form['leave_emp_id']
        leave_startdate = request.form['leave_leave_startdate']
        leave_enddate = request.form['leave_enddate']
        leave_description = request.form['leave_description']
        leave_status = " "
        leave_statusdate = dt.datetime.now().strftime(format="%d-%b-%Y")
        leave_statustime = dt.datetime.now().strftime(format="%H:%M:%S")
        
        return render_template('leave-output.html', leave_output_title = 'Employee Leave Added Unsuccessfully')

@app.route("/leave/view", methods=['GET','POST'])
def leaveview():
    cursor = db_conn.cursor()
    select_leaveview_sql = "SELECT * FROM leavetest"

    try:
        cursor.execute(select_leaveview_sql)
        leave_view = []
        i = 0
        while True:
            leave_view_data = cursor.fetchone()
            if leave_view_data is None:
                break
            else:
                leave_view.append(leave_view_data)
            i += 1
    finally:
        cursor.close()
          
    return render_template('leave-view.html', leave_view=leave_view)


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
