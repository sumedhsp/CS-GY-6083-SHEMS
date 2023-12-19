from django.shortcuts import render, redirect
from django.http import HttpResponse
from django.contrib.auth.models import User
from django.contrib import messages
from django.core.mail import EmailMessage, send_mail
from django.contrib.sites.shortcuts import get_current_site
from django.template.loader import render_to_string
from django.utils.http import urlsafe_base64_decode, urlsafe_base64_encode
# from django.utils.encoding import force_bytes, force_text
from django.contrib.auth import authenticate, login, logout
from datetime import datetime
from . tokens import generate_token

# Importing the necessary models
from .models import Customers
from .models import Servicelocations
from .models import Enrolleddevices

# Create your views here.
# def home(request):
#   return render(request, 'accounts/homepage.html', {'today': datetime.today()})
  # return HttpResponse('Hello Customer, Welcome to Smart Home Energy Management System powered by NYU Folks!!!!!!')


def devices(request):
    return render(request, "accounts/devices.html", {})


def home(request):
    return render(request, "accounts/index.html", {'today': datetime.today()})

def signup(request):
    if request.method == "POST":
        username = request.POST['username']
        fname = request.POST['fname']
        lname = request.POST['lname']
        email = request.POST['email']
        pass1 = request.POST['pass1']
        pass2 = request.POST['pass2']
        
        if User.objects.filter(username=username):
            messages.error(request, "Username already exist! Please try some other username.")
            return redirect('home')
        
        if User.objects.filter(email=email).exists():
            messages.error(request, "Email Already Registered!!")
            return redirect('home')
        
        if len(username)>20:
            messages.error(request, "Username must be under 20 charcters!!")
            return redirect('home')
        
        if pass1 != pass2:
            messages.error(request, "Passwords didn't matched!!")
            return redirect('home')
        
        if not username.isalnum():
            messages.error(request, "Username must be Alpha-Numeric!!")
            return redirect('home')
        
        myuser = User.objects.create_user(username, email, pass1)
        myuser.first_name = fname
        myuser.last_name = lname
        myuser.is_active = True
        myuser.save()
        messages.success(request, "Your Account has been created succesfully!")
        
        return redirect('signin')
        
        
    return render(request, "accounts/signup.html")


def signin(request):
    # Writing all the queries here for testing.
    # Need to organize them better. Check online or ask Sriphani how to organize the files better. 
    # Probably in a class?
    
    # Need to change the customer_id here.
    customerObject = Customers.objects.raw("Select * from Customers C join Address A on C.billing_address_id = A.address_id where customer_id = 1 ")
    serviceLocationObject = Servicelocations.objects.raw("Select * from ServiceLocations SL join Address A on SL.address_id = A.address_id  where customer_id = 1 ")
    enrolledDevicesCountObject =  Servicelocations.objects.raw(""" Select SL.sl_id, count(*) AS num_Devices from EnrolledDevices ED 
		 join ServiceLocations SL on ED.sl_id = SL.sl_id 
		 where customer_id = 1
		 group by SL.sl_id""")
    
    # Customized logic to combine the rows
    combined_object = []
    for i in range(len(serviceLocationObject)):
        combined_object.append({'serviceLocation':serviceLocationObject[i], 'device_count':enrolledDevicesCountObject[i].num_devices})

    return render(request, "accounts/index.html", {"customerObject": customerObject[0],
                                                   "serviceLocationObject": combined_object})
    if request.method == 'POST':
        username = request.POST['username']
        pass1 = request.POST['pass1']
        
        user = authenticate(username=username, password=pass1)
        
        if user is not None:
            login(request, user)
            fname = user.first_name
            # messages.success(request, "Logged In Sucessfully!!")
            return render(request, "accounts/index.html",{"fname":fname})
        else:
            messages.error(request, "Bad Credentials!!")
            return redirect('home')
    
    return render(request, "accounts/signin.html",{'today': datetime.today()})


def signout(request):
    logout(request)
    messages.success(request, "Logged Out Successfully!!")
    return redirect('home')