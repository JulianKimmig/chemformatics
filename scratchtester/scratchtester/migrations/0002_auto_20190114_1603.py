# Generated by Django 2.1.2 on 2019-01-14 15:03

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [("scratchtester", "0001_initial")]

    operations = [
        migrations.AlterField(
            model_name="measurement",
            name="raw_data",
            field=models.FilePathField(default=None, null=True),
        )
    ]