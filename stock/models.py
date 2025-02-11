from django.contrib.auth.models import User
from django.db import models

class Company(models.Model):
    ticker = models.CharField(primary_key=True, max_length=20)
    name = models.CharField(max_length=100, null=True, blank=True)
    sector = models.CharField(max_length=200, null=True, blank=True)
    industry = models.CharField(max_length=200, null=True, blank=True)
    location = models.CharField(max_length=100, null=True, blank=True)
    entry_date = models.DateField(null=True)
    cik_key = models.CharField(max_length=10, null=True, blank=True)
    founded_year = models.DateField(null=True)
    created_ts = models.DateTimeField(auto_now_add=True)
    updated_ts = models.DateTimeField(auto_now=True)

class UserStock(models.Model):
    ticker = models.CharField(max_length=20, unique=True)
    user = models.ManyToManyField(User)