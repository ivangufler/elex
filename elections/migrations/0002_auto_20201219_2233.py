# Generated by Django 3.1.4 on 2020-12-19 22:33

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('elections', '0001_initial'),
    ]

    operations = [
        migrations.RenameField(
            model_name='election',
            old_name='admin',
            new_name='owner',
        ),
    ]