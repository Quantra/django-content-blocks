# Generated by Django 4.2.6 on 2023-10-19 14:22

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_blocks', '0005_alter_contentblockcollection_options'),
    ]

    operations = [
        migrations.CreateModel(
            name='IframeField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.AddField(
            model_name='contentblockfield',
            name='iframe',
            field=models.CharField(blank=True, max_length=256),
        ),
    ]
