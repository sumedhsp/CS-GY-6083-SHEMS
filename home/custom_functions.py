
# For sessions
from django.contrib.sessions.models import Session


def home_page(Customers, Servicelocations, username):
    customerObjects = Customers.objects.raw("Select * from Customers C join Address A on C.billing_address_id = A.address_id where C.email = %s ", [username])
    customerObject = customerObjects[0]
    
    serviceLocationObject = Servicelocations.objects.raw("Select * from ServiceLocations SL join Address A on SL.address_id = A.address_id  where customer_id = %s ", [customerObject.customer_id])
    enrolledDevicesCountObject =  Servicelocations.objects.raw(""" Select SL.sl_id, count(ED.enrolled_device_id) AS num_Devices from EnrolledDevices ED 
                right join ServiceLocations SL on ED.sl_id = SL.sl_id 
                where customer_id = %s
                group by SL.sl_id""", [customerObject.customer_id])

    combined_object = []
    for i in range(len(serviceLocationObject)):
        combined_object.append({'serviceLocation':serviceLocationObject[i], 'device_count':enrolledDevicesCountObject[i].num_devices})

    return customerObject, combined_object


def display_devices(Servicelocations, Enrolleddevices, sl_id):
     serviceLocationObject = Servicelocations.objects.raw("Select * from ServiceLocations SL join Address A on SL.address_id = A.address_id  where SL.sl_id = %s ", [sl_id])
     enrolledDeviceObjects = Enrolleddevices.objects.raw("Select * from EnrolledDevices ED join Device D on ED.model_id = D.model_id where ED.sl_id = %s ", [sl_id])
     return serviceLocationObject[0], enrolledDeviceObjects



def delete_session(request):
    
    session_key = request.session.session_key
    Session.objects.raw("Delete from Sessions where session_key = %s",[session_key])

    request.session.flush()

    return