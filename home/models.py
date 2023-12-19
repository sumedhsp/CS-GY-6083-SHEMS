from django.db import models

# Create your models here.
class Address(models.Model):
    address_id = models.AutoField(primary_key=True)
    unit_number = models.CharField(max_length=50)
    address_line = models.CharField(max_length=100)
    city = models.CharField(max_length=50)
    state = models.CharField(max_length=30)
    zipcode = models.IntegerField()

    class Meta:
        managed = False
        db_table = 'address'


class Customers(models.Model):
    customer_id = models.AutoField(primary_key=True)
    first_name = models.CharField(max_length=100, null=True)
    last_name = models.CharField(max_length=100)
    billing_address = models.ForeignKey(Address, models.DO_NOTHING)

    #additional fields
    email = models.CharField(max_length=50, null=True)
    registered_date = models.DateTimeField(auto_now_add=True)

    class Meta:
        managed = False
        db_table = 'customers'


class Device(models.Model):
    model_id = models.CharField(primary_key=True, max_length=100)
    device_type = models.CharField(max_length=100)
    model_number = models.CharField(max_length=100)
    brand = models.CharField(max_length=100, blank=True, null=True)
    release_year = models.IntegerField(blank=True, null=True)
    manufacture_year = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'device'


class Devicedata(models.Model):
    data_id = models.AutoField(primary_key=True)
    enrolled_device = models.ForeignKey('Enrolleddevices', models.DO_NOTHING)
    event_timestamp = models.DateTimeField(blank=True, null=True)
    event_label = models.CharField(max_length=100)
    event_value = models.DecimalField(max_digits=18, decimal_places=6, blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'devicedata'


class Energyprices(models.Model):
    zipcode = models.IntegerField(primary_key=True)  # The composite primary key (zipcode, price_timestamp) found, that is not supported. The first column is selected.
    price_timestamp = models.DateTimeField()
    price_per_kwh = models.DecimalField(max_digits=18, decimal_places=6)

    class Meta:
        managed = False
        db_table = 'energyprices'
        unique_together = (('zipcode', 'price_timestamp'),)


class Enrolleddevices(models.Model):
    enrolled_device_id = models.AutoField(primary_key=True)
    sl = models.ForeignKey('Servicelocations', models.DO_NOTHING)
    model = models.ForeignKey(Device, models.DO_NOTHING)

    class Meta:
        managed = False
        db_table = 'enrolleddevices'


class Servicelocations(models.Model):
    sl_id = models.AutoField(primary_key=True)
    customer = models.ForeignKey(Customers, models.DO_NOTHING, blank=True, null=True)
    address = models.ForeignKey(Address, models.DO_NOTHING, blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    apt_area = models.DecimalField(max_digits=18, decimal_places=6, blank=True, null=True)
    num_bedrooms = models.IntegerField(blank=True, null=True)
    num_occupants = models.IntegerField(blank=True, null=True)

    class Meta:
        managed = False
        db_table = 'servicelocations'
