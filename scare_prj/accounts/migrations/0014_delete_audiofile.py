# Generated by Django 5.0.7 on 2024-08-05 18:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0013_remove_audiofile_description_remove_audiofile_file_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='AudioFile',
        ),
    ]
