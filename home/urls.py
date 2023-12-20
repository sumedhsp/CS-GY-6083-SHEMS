from django.urls import path

from . import views



urlpatterns = [
  
    path('', views.home, name='home'),
    #path('home/', views.home, name='home'),

    path('signup/', views.signup, name='signup'),
    # path('activate/<uidb64>/<token>', views.activate, name='activate'),
    path('signin/', views.signin, name='signin'),
    path('signout/', views.signout, name='signout'),

    path('devices/', views.devices, name='devices'),

    path('analytics/', views.plotChart, name='analytics'),

    #path('pie_chart/', views.plotChart, name='charts'),

    # This path is just to save the device data into the EnrolledDevice Table
    path('addDevice/', views.addDevices, name='addDevices'),

    path('addServiceLocation/', views.addServiceLocation, name='addServiceLocation'),
    
    path('displayDevices/', views.displayDevices, name='displayDevices'),

    path('deviceType/', views.getDeviceType, name='get_device_type'),

    path('changePassword/', views.changePassword, name='change_password'),

    path('editProfile/', views.editProfile, name='edit_profile'),

    path('deleteServiceLocation/', views.deleteServiceLocation, name='delete_service_location'),

    path('editServiceLocation/', views.editServiceLocation, name='edit_service_location'),

    path('getServiceLocations/', views.getServiceLocations, name='get_service_location')

]