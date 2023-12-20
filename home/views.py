import hashlib
import pandas as pd
from django.shortcuts import render, redirect
from django.http import HttpResponse, JsonResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# from django.utils.encoding import force_bytes, force_text
from django.contrib.auth import authenticate, login, logout
from datetime import datetime

#from .home import delete_session
from . tokens import generate_token

# For Transactions
from django.db import connection, transaction

# Importing the necessary models
from .models import Customers, Device, Devicedata
from .models import Servicelocations
from .models import Enrolleddevices



# Importing plotly
import plotly.express as px

from home.custom_functions import home_page, display_devices, delete_session

def devices(request):
    return render(request, "accounts/devices.html", {})


def home(request):
    user_active = False
    if (request.session.session_key is not None and
        request.session['username']):
        user_active = True

        customerObject, combined_object = home_page(Customers, Servicelocations, request.session['username'])
            
        return render(request, "accounts/index.html", {"customerObject": customerObject,
                                                        "serviceLocationObject": combined_object,
                                                        "user_active": True})

    return render(request, "accounts/index.html", {"today": datetime.today(),
                                                   "user_active": user_active})

def signup(request):
    if (request.session.get('username', None) is not None):
        return redirect('home')

    if request.method == "POST":
        fname = request.POST['fname']
        lname = request.POST['lname']
        # The username is email!!
        username = request.POST['email']
        password = request.POST['pass1']
        # Do we need to check the pass2 detail?
        pass2 = request.POST['pass2']

        phone_num = request.POST['phone']
        dob = request.POST['dob']
        unit_number = request.POST['unitno']
        address_line = request.POST['addline']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zip']
        
        if Customers.objects.raw("Select customer_id from Customers where email = %s", [username]):
            messages.error(request, "Username already exists! Please try some other username.")
            return render(request, 'accounts/signup.html')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 characters!!")
            return render(request, 'accounts/signup.html')
        
        if password != pass2:
            messages.error(request, "Passwords don't matched!!")
            return render(request, 'accounts/signup.html')
        
        if (len(zipcode) > 5):
            messages.error(request, "Zipcode format is incorrect")
            return render(request, 'accounts/signup.html')

        if (len(state) != 2):
            messages.error(request, "Please enter the code for state")
            return render(request, 'accounts/signup.html')
        
        if (len(phone_num) != 10):
            messages.error(request, "Phone number is incorrect")
            return render(request, 'accounts/signup.html')

        # Create a Transaction
        rows_affected = 0
        with connection.cursor() as cursor:
            # Should we be using transaction at native SQL or this is fine?
            try:
                with transaction.atomic(using='default'):
                    address_insert = "INSERT INTO ADDRESS (unit_number, address_line, city, state, zipcode) values(%s, %s, %s, %s, %s) RETURNING address_id"
                    cursor.execute(address_insert, [unit_number, address_line, city, state, zipcode])

                    billing_id = cursor.fetchone()

                    customer_insert = """INSERT INTO CUSTOMERS (email, password, phone_num, dob, first_name, last_name, billing_address_id) 
                                        values(%s, crypt(%s, gen_salt('bf')), %s, %s, %s, %s, %s)"""
                    cursor.execute(customer_insert, [username, password, phone_num, dob, fname, lname, billing_id])

                    rows_affected = cursor.rowcount

            # Abort the transaction
            except Exception as e:
                messages.error(request, "Error occurred while saving. Please try again after sometime")

        if (rows_affected == 1):
            messages.success(request, "Your Account has been created succesfully!")
            # Need to redirect to dashboard.
            return redirect('signin')
        else:
            messages.error(request, "Failed to create the account. Please try again after sometime")
        
        
    return render(request, "accounts/signup.html")


def signin(request):
    # Login page
    if (request.session.get('username', None) is not None):
        return redirect('home')

    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']

        with connection.cursor() as cursor:
            try:
                login_query = " SELECT  1 FROM CUSTOMERS where email = %s and password = crypt(%s, password) "
                cursor.execute(login_query, [username, pass1])

                is_valid = cursor.fetchone()

            except Exception as e:
                messages.error(request, "Error while logging in the user")


        if (is_valid):
            # Need to create sessions now, to manage concurrency before this condition.
            # Creating a session
            request.session['username'] =  username
            
            token = hashlib.sha256(str(request.user.id).encode('utf-8')).hexdigest()

            # Writing all the queries here for testing.
            # Need to organize them better. Check online or ask Sriphani how to organize the files better. 
            # Probably in a class?
            
            # Need to change the customer_id here.
            customerObject, combined_object = home_page(Customers, Servicelocations, username)
            # Initializing the session for customer_id
            request.session['customer_id'] = customerObject.customer_id
            return render(request, "accounts/index.html", {"customerObject": customerObject,
                                                           "serviceLocationObject": combined_object,
                                                           "user_active": True,
                                                           "token": token})

        else:
            messages.error(request, "Invalid credentials")
            return render(request, 'accounts/signin.html', {'today': datetime.today()})
    
    # Main Login Page
    return render(request, "accounts/signin.html",{'today': datetime.today()})

def signout(request):

    delete_session(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')




def addServiceLocation(request):
    if (request.session.get('username', None) is None):
        return redirect('home')

    if request.method == 'POST':
        service_location_label = request.POST['slLabel']
        start_date = request.POST['startDate']
        unit_no = request.POST['unitno']
        area = request.POST['area']
        num_beds = request.POST['bedno']
        occ_num = request.POST['occno']
        addressLine = request.POST['addline']
        city = request.POST['city']
        state = request.POST['state']
        zipcode = request.POST['zip']
        customer_id = request.POST['customer_id']

        service_location_insert_q = """ 
            INSERT INTO ServiceLocations(customer_id,address_id,service_location_label,start_date,apt_area,num_bedrooms,num_occupants) 
            values(%s,%s,%s,%s,%s,%s,%s) 
"""
        rows_affected = 0
        with connection.cursor() as cursor:
            with transaction.atomic(using='default'):
                try:
                    address_insert = "INSERT INTO ADDRESS (unit_number, address_line, city, state, zipcode) values(%s, %s, %s, %s, %s) RETURNING address_id"
                    cursor.execute(address_insert, [unit_no, addressLine, city, state, zipcode])

                    address_id = cursor.fetchone()

                    cursor.execute(service_location_insert_q, [customer_id, address_id, service_location_label, start_date, area, num_beds, occ_num])

                    rows_affected = cursor.rowcount
                except Exception as e:
                    messages.error(request, "Error while inserting data")
        
        if (rows_affected == 1):
            username = request.session['username']

            # Need to change the customer_id here.
            customerObject, combined_object = home_page(Customers, Servicelocations, username)

            return render(request, 'accounts/index.html', {"customerObject": customerObject,
                                                           "serviceLocationObject": combined_object,
                                                           "user_active": True})
        # Add logic to save the details for ServiceLocation     
    
    return redirect('home')   


def addDevices(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    if request.method == 'POST':
        model_id = request.POST['devtype']
        sl_id = request.POST['sl_id']

        quickAddRef = request.POST.get('quickAddReference')

        rowsAffected = 0
        with connection.cursor() as cursor:
            try:
                enrolled_device_insert = "INSERT into EnrolledDevices(sl_id, model_id) values(%s, %s) "
                cursor.execute(enrolled_device_insert, [sl_id, model_id])

                rowsAffected = cursor.rowcount
                if rowsAffected == 1:
                    messages.success(request, "Added the device to your Service Location successfully")
                    if (quickAddRef):
                        return redirect('home')
                    else:
                        request.session['displayDevicesData'] = sl_id
                        return redirect('displayDevices')
            except Exception as e:
                messages.error(request, "Error while inserting devices")

    return redirect('home')

def displayDevices(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    any_prev_data = request.session.pop('displayDevicesData', None)
    if request.method == 'POST' or any_prev_data:
        sl_id = None
        if any_prev_data:
            sl_id = any_prev_data
        else:
            sl_id = request.POST['sl_id']
        # Display Devices

        # Remove the hard-code for Service Location ID
        serviceLocationObject, enrolledDeviceObjects = display_devices(Servicelocations, Enrolleddevices, sl_id)
        user_active = False
        if (request.session.session_key is not None and
            request.session['username']):
            user_active = True

        return render(request, 'accounts/devices.html', {'serviceLocationObject':serviceLocationObject,
                                                         'enrolledDeviceObjects': enrolledDeviceObjects,
                                                         'user_active': user_active})
    return redirect('home')

def getDeviceType(request):

    deviceTypeObject = Device.objects.raw("Select * from device ")

    l = []
    for i in range(len(deviceTypeObject)):
        l.append(str(deviceTypeObject[i].model_id) + ":" + deviceTypeObject[i].device_type + "," + deviceTypeObject[i].model_number + "," + deviceTypeObject[i].brand + "," + str(deviceTypeObject[i].release_year) + "," + str(deviceTypeObject[i].manufacture_year))
    
    return JsonResponse(list(l), safe=False)


def changePassword(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    if request.method == 'POST':
        new_password = request.POST['newpassword']
        customer_id = request.POST['customer_id']

        update_password_query = "Update Customers set password = crypt(%s, gen_salt('bf')) where customer_id = %s"
        rows_affected = 0
        with connection.cursor() as cursor:
            try:
                cursor.execute(update_password_query, [new_password, customer_id])

                rows_affected = cursor.rowcount

                if (rows_affected == 1):
                    messages.success(request, "Password is updated for your account")
                else:
                    messages.error(request, "Failed to update the password. Please try again")

            except Exception as e:
                messages.error(request, "Error while updating the password")

    return redirect('home') 


def editProfile(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    if request.method == "POST":
        customer_id = request.POST['customer_id']
        first_name = request.POST['fname']
        last_name = request.POST['lname']
        phone_num = request.POST['phone']

        edit_profile_query = "Update Customers set "
        parameterized_list = []
        if (first_name != ""):
            edit_profile_query += " first_name = %s"
            parameterized_list.append(first_name)

        if (last_name != ""):
            if (len(parameterized_list) > 0):
                edit_profile_query += ", "
            edit_profile_query += " last_name = %s"
            parameterized_list.append(last_name)

        if (phone_num != ""):
            if (len(parameterized_list) > 0):
                edit_profile_query += ", "
            edit_profile_query += " phone_num = %s " 
            parameterized_list.append(phone_num)

        edit_profile_query += " where customer_id = %s"
        if (len(parameterized_list) == 0):
            return redirect('home')
        
        parameterized_list.append(customer_id)
        rows_affected = 0
        with connection.cursor() as cursor:
            try:
                cursor.execute(edit_profile_query, parameterized_list)

                rows_affected = cursor.rowcount
                if (rows_affected == 1):
                    messages.success(request, "Updated the profile details successfully")
                else:
                    messages.error(request, "Unable to update the records")

            except Exception as e:
                messages.error(request, "Error occured while updating records")

    return redirect('home')


def deleteServiceLocation(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    if request.method == "POST":
        sl_id = request.POST['sl_id']

        delete_query = " Delete from ServiceLocations where sl_id = %s"

        rows_affected = 0
        with connection.cursor() as cursor:
            try:    
                cursor.execute(delete_query, [sl_id])

                rows_affected = cursor.rowcount
                if (rows_affected == 1):
                    messages.success(request, "Service Location record is deleted successfully")
                else:
                    messages.error(request, "Unable to delete the Service Location record")

            except Exception as e:
                messages.error(request, "Error occured while deleting the service location")

    return redirect('home')


def editServiceLocation(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    if request.method == 'POST':
        area = request.POST['area']
        num_beds = request.POST['bedno']
        num_occupants = request.POST['occno']
        sl_id = request.POST['sl_id']

        edit_service_data = "Update ServiceLocations set "
        parameterized_list = []
        if (area != ""):
            edit_service_data += " apt_area = %s"
            parameterized_list.append(area)

        if (num_beds != ""):
            if (len(parameterized_list) > 0):
                edit_profile_query += ", "
            edit_service_data += " num_bedrooms = %s"
            parameterized_list.append(num_beds)

        if (num_occupants != ""):
            if (len(parameterized_list) > 0):
                edit_profile_query += ", "
            edit_service_data += " num_occupants = %s " 
            parameterized_list.append(num_occupants)

        edit_service_data += " where sl_id = %s"
        if (len(parameterized_list) == 0):
            return displayDevices(request, sl_id)
        
        parameterized_list.append(sl_id)
        rows_affected = 0
        with connection.cursor() as cursor:
            try:
                
                cursor.execute(edit_service_data, parameterized_list)

                rows_affected = cursor.rowcount
                if (rows_affected == 1):
                    messages.success(request, "Updated the Service Location details successfully")
                else:
                    messages.error(request, "Unable to update the Service Location records")

            except Exception as e:
                messages.error(request, "Error occured while updating the Service Location records")

    
    request.session['displayDevicesData'] = sl_id
    return redirect('displayDevices')

def analytics(request):

    return HttpResponse("Analytics page")


def getServiceLocations(request):

    customer_id = request.session.get('customer_id', None)
    if (customer_id == None):
        return
    
    serviceLocationObject = Servicelocations.objects.raw(" Select sl_id, service_location_label from servicelocations where customer_id = %s",[customer_id])

    l = []
    for i in range(len(serviceLocationObject)):
        l.append(str(serviceLocationObject[i].sl_id) + "-" + serviceLocationObject[i].service_location_label)

    return JsonResponse(list(l), safe=False)

# Plotting the charts


def plotChart(request):
    if (request.session.get('username', None) is None):
        return redirect('home')
    
    aformdictionary =dict()
    # = dict(year="2023", sdate="12-23-1999", edate="12-23-2023")

    if request.method == 'POST':
        aformdictionary['atype'] = request.POST.get('atype')    
        aformdictionary['sloc'] = request.POST.get('sloc')
        aformdictionary['year'] = request.POST.get('year')
        aformdictionary['sdate'] = request.POST.get('sdate')
        aformdictionary['edate'] = request.POST.get('edate')
        customer_id = request.POST.get('customer_id')
        sl_id = request.POST.get('sl_id')

    if (aformdictionary['atype'] is None):
        aformdictionary = dict(atype="1", year="2023", sdate="12-23-1999", edate="12-23-2023")


    chart_json_pie = ''
    chart_json_bar = ''
    chart_json_line = ''
    chart_json_stacked_bar = ''
        

    q1="""SELECT
                        D.device_type,
                        SUM(DD.event_value) AS total_energy
                    FROM
                        DeviceData DD
                    JOIN EnrolledDevices ED ON DD.enrolled_device_id = ED.enrolled_device_id
                    JOIN Device D ON ED.model_id = D.model_id
                    JOIN ServiceLocations SL ON ED.sl_id = SL.sl_id
                    WHERE
                        SL.customer_id = %s
                        AND DD.event_label = 'energy use'
                        AND EXTRACT(YEAR FROM DD.event_timestamp) = %s
                    GROUP BY
                        D.device_type"""
        
    q2="""
            SELECT
            extract('hour' from DD.event_timestamp) AS hour_of_event,
                SUM(DD.event_value) AS total_energy
            FROM
                DeviceData DD
            JOIN EnrolledDevices ED ON DD.enrolled_device_id = ED.enrolled_device_id
            JOIN ServiceLocations SL ON ED.sl_id = SL.sl_id
            WHERE
                SL.customer_id = %s
                AND DD.event_label = 'energy use'
                AND SL.sl_id = %s
                AND DD.event_timestamp >= %s and DD.event_timestamp <= %s            
				GROUP BY
                hour_of_event
            ORDER BY
                hour_of_event;

        """
    q3a="""
                    SELECT
            extract('hour' from DD.event_timestamp) AS hour_of_event,
                SUM(DD.event_value) AS total_energy
            FROM
                DeviceData DD
            JOIN EnrolledDevices ED ON DD.enrolled_device_id = ED.enrolled_device_id
            JOIN ServiceLocations SL ON ED.sl_id = SL.sl_id
            WHERE
                SL.customer_id = %s
                AND DD.event_label = 'energy use'
                AND SL.sl_id = %s
                AND DD.event_timestamp >= %s and DD.event_timestamp <= %s            
				GROUP BY
                hour_of_event
            ORDER BY
                hour_of_event;

        """
    
    q3b="""
                    Select extract('hour' from DD.event_timestamp) AS hour_of_event, avg(DD.event_value) AS avg_energy from DeviceData DD
        join EnrolledDevices ED on DD.enrolled_device_id = ED.enrolled_device_id
        join ServiceLocations SL on ED.sl_id = SL.sl_id
        join Address A on A.address_id = SL.address_id
        where SL.customer_id = %s and
                DD.event_label = 'energy use' AND
                DD.event_timestamp >= %s and DD.event_timestamp <= %s and
                A.zipcode = (Select A1.zipcode from Address A1 join ServiceLocations SL1 on A1.address_id = SL1.address_id where SL1.sl_id = %s)
        group by hour_of_event
                ORDER BY
                hour_of_event;

        """
    
    q4="""
                        SELECT
                        D.device_type,SL.sl_id,
                        SUM(DD.event_value) AS total_energy
                    FROM
                        DeviceData DD
                    JOIN EnrolledDevices ED ON DD.enrolled_device_id = ED.enrolled_device_id
                    JOIN Device D ON ED.model_id = D.model_id
                    JOIN ServiceLocations SL ON ED.sl_id = SL.sl_id
                    WHERE
                        SL.customer_id = %s
                        AND DD.event_label = 'energy use'
                        AND EXTRACT(YEAR FROM DD.event_timestamp) = %s
                    GROUP BY
                        D.device_type,SL.sl_id

        """
    q5 = """
                    Select zipcode, avg(price_per_kwh) from Energy_Prices group by zipcode
        """     
    analyticsType=aformdictionary['atype']

    if analyticsType=='1':
        with connection.cursor() as cursor:
            cursor.execute(q1, [customer_id, aformdictionary['year']])
            dataq1 = cursor.fetchall()
        

        xaxis = []
        yaxis = [] 
        for i in range(len(dataq1)):
            xaxis.append(dataq1[i][0])
            yaxis.append(dataq1[i][1])

        dataq1 = {"DeviceType": xaxis, "EnergyConsumption": yaxis}
        print('came here',dataq1)

       # Bar Chart

        fig_bar_q1 = px.bar(dataq1, x='DeviceType', y='EnergyConsumption', title='Device Type Vs Energy Consumption')
        fig_bar_q1.update_layout(xaxis_title='Device Type', yaxis_title='Energy Consumption', height=600)

        # Customizing colors and adding title in the middle
        colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']  # Add more colors if needed
        fig_bar_q1.update_traces(marker_color=colors)

        # Adding title in the middle
        fig_bar_q1.update_layout(
        title_text="Device Type Vs Energy Consumption",
        title_x=0.5,  # Set the title to the middle of the chart
        )
        chart_json_bar = fig_bar_q1.to_html()
    

    elif analyticsType=='2':
        with connection.cursor() as cursor:
            cursor.execute(q2, [customer_id, sl_id, aformdictionary['sdate'], aformdictionary['edate']])
            dataq2 = cursor.fetchall()

        xaxis = []
        yaxis = [] 
        for i in range(len(dataq2)):
            xaxis.append(dataq2[i][0])
            yaxis.append(dataq2[i][1])

        dataq2=  {"TimeInHours": xaxis, "EnergyConsumption": yaxis}

        # Line Chart
        fig_line_q2 = px.line(dataq2, x='TimeInHours', y='EnergyConsumption',
                            title='SL based Time Vs Energy Consumption')
        fig_line_q2.update_layout(height=600)

        # Adding title in the middle
        fig_line_q2.update_layout(
        title_text="SL based Time Vs Energy Consumption",
        title_x=0.5,  # Set the title to the middle of the chart
        )
        chart_json_bar = fig_line_q2.to_html()
    
            
    elif analyticsType=='3':
        with connection.cursor() as cursor:
            cursor.execute(q3a, [customer_id, sl_id, aformdictionary['sdate'], aformdictionary['edate']])
            dataq3a = cursor.fetchall()
            cursor.execute(q3b, [customer_id, aformdictionary['sdate'], aformdictionary['edate'], sl_id])
            dataq3b = cursor.fetchall()

        xaxisA = []
        yaxisA = [] 
        xaxisB = []
        yaxisB = []
        for i in range(len(dataq3a)):
            xaxisA.append(dataq3a[i][0])
            yaxisA.append(dataq3a[i][1])

        for i in range(len(dataq3b)):
            xaxisB.append(dataq3b[i][0])
            yaxisB.append(dataq3b[i][1])

        # Create dictionaries for each dataset
        dataq3a = {"TimeInHours": xaxisA, "EnergyConsumption": yaxisA}
        dataq3b = {"TimeInHours": xaxisB, "EnergyConsumption": yaxisB}

        # Line Chart
        fig_line_q3 = px.line(dataq3a, x='TimeInHours', y='EnergyConsumption', 
                            title='Your Energy Consumption VS Avg Energy Consumption in your Area', 
                            line_shape='linear', labels={'EnergyConsumption': 'Energy Consumption'})
        fig_line_q3.add_scatter(x=dataq3b['TimeInHours'], y=dataq3b['EnergyConsumption'], 
                                mode='lines', name='Avg', line=dict(color='orange'))
        fig_line_q3.add_scatter(x=dataq3a['TimeInHours'], y=dataq3a['EnergyConsumption'], 
                                mode='lines', name='Actual', line=dict(color='blue'))
        

        fig_line_q3.update_layout(height=600)

        # Adding title in the middle
        fig_line_q3.update_layout(
            title_text="Your Actual Energy Consumption VS Avg Energy Consumption in your Area",
            title_x=0.5,  # Set the title to the middle of the chart
        )

        chart_json_bar = fig_line_q3.to_html()

    elif analyticsType=='5':
        # Enery Prices plot
        with connection.cursor() as cursor:
            cursor.execute(q5)
            dataq5 = cursor.fetchall()
            
            zipcodes = []
            avg_energy_prices = []
            for i in range(len(dataq5)):
                zipcodes.append(dataq5[i][0])
                avg_energy_prices.append(dataq5[i][1])
        
        df = pd.DataFrame({
            'Zipcode':zipcodes,
            'Avg Energy Price':avg_energy_prices
        })
        fig_pie = px.pie(df, names='Zipcode', values='Avg Energy Price')
        fig_pie.update_layout(title_text=" Pie chart of the average energy prices in different zipcodes",title_x=0.5, height=600)

        
        chart_json_pie = fig_pie.to_html()

            
    else:

        with connection.cursor() as cursor:
            cursor.execute(q4, [customer_id, aformdictionary['year']])
            dataq4 = cursor.fetchall()
        

        xaxis = []
        yaxis = [] 
        stackSlid = []
        for i in range(len(dataq4)):
            xaxis.append(dataq4[i][0])
            yaxis.append(dataq4[i][2])
            stackSlid.append(dataq4[i][1])

        dataq4 = {"DeviceType": xaxis, "EnergyConsumption": yaxis , "Slid": stackSlid}
        print (dataq4)
       # Bar Chart
        fig_bar_q4 = px.bar(dataq4, x='DeviceType', y='EnergyConsumption', color='Slid',
                            title='Energy Consumption Per Device Type Per SL',
                            labels={'TotalEnergy': 'Energy Consumption'},
                            barmode='stack', hover_data=['Slid'])  # Adjust the number of columns as needed

        fig_bar_q4.update_layout(height=600)

        # Adding title in the middle
        fig_bar_q4.update_layout(
        title_text="Energy Consumption Per Device Type Per SL",
        title_x=0.5,  # Set the title to the middle of the chart
        showlegend=True,
        )
        chart_json_bar = fig_bar_q4.to_html()
            



    
    # with connection.cursor() as cursor:
    #     cursor.execute(q2, [aformdictionary['sdate'], aformdictionary['edate']])
    #     dataq2 = cursor.fetchall()

    # xaxis = [] #1,2,3, 5,5,7,8,9,9]
    # yaxis = [] #1,2,3, 5,5,7,8,9,9]
    # for i in range(len(dataq2)):
    #     xaxis.append(dataq2[i][0])
    #     yaxis.append(dataq2[i][1])

    # dataq1 = {"DeviceType": xaxis, "EnergyConsumption": yaxis}
    # dataq2=  {"TimeInHours": xaxis, "EnergyConsumption": yaxis}



    #pie chart
    # fig = px.pie(dataq1, names='DeviceType', values='EnergyConsumption', title='Pie Chart Example')


 


    

    # Stacked Bar Chart
    # fig_stacked_bar = px.bar(stk_data, x='DeviceType', y=['Category1', 'Category2', 'Category3'],
    #                      title='Stacked Bar Chart Example', barmode='stack')

    user_active = False
    if (request.session.session_key is not None and
        request.session['username']):
        user_active = True

    return render(request, 'accounts/analytics.html', 
                  {'chart_json_pie': chart_json_pie,
                   'chart_json_bar': chart_json_bar, 
                   'chart_json_line': chart_json_line, 
                   'chart_json_stacked_bar': chart_json_stacked_bar,
                   'aformdictionary':aformdictionary,
                   'user_active': user_active,
                   'customer_id': customer_id,
                   'sl_id': sl_id})

