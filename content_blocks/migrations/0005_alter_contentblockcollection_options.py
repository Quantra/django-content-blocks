# Generated by Django 4.2.1 on 2023-09-04 22:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('content_blocks', '0004_remove_contentblocktemplate_no_cache'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='contentblockcollection',
            options={'ordering': ['name']},
        ),
    ]
