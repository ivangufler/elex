from django.db import models
from django.contrib.auth.models import User
from django.utils import timezone


class Election(models.Model):
    name = models.CharField(max_length=255)
    description = models.CharField(max_length=500, blank=True, default='')
    owner = models.ForeignKey(
        User, on_delete=models.DO_NOTHING
    )
    paused = models.BooleanField(default=False)
    votable = models.IntegerField(default=1)
    voters = models.IntegerField(default=0)
    voted = models.IntegerField(default=0)
    creation_date = models.DateTimeField(default=timezone.now)
    start_date = models.DateTimeField(null=True, default=None)
    end_date = models.DateTimeField(null=True, default=None)


class Option(models.Model):
    name = models.CharField(max_length=255, primary_key=True)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE
    )
    votes = models.IntegerField(default=0)

    class Meta:
        managed = False
        db_table = 'elections_option'


class Voter(models.Model):
    token = models.CharField(unique=True, max_length=255)
    email = models.EmailField(max_length=255, primary_key=True)
    election = models.ForeignKey(
        Election, on_delete=models.CASCADE
    )
    voted = models.BooleanField(default=False)

    class Meta:
        managed = False
        db_table = 'elections_voter'
