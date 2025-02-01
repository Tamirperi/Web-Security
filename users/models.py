from django.db import models

# Create your models here.


# טבלת משתמשים
class User(models.Model):
    username = models.CharField(max_length=150, unique=True)
    password = models.CharField(max_length=255)  # סיסמאות יישמרו בצורה מאובטחת
    email = models.EmailField(unique=True)

    def __str__(self):
        return self.username

# טבלת לקוחות
class Customer(models.Model):
    full_name = models.CharField(max_length=255)  # שם מלא
    phone_number = models.CharField(max_length=15)  # מספר טלפון
    address = models.TextField()  # כתובת

    def __str__(self):
        return self.full_name
