# Generated by Django 4.1.7 on 2023-03-17 11:59

import content_blocks.fields
import content_blocks.models
import django.core.validators
from django.db import migrations, models
import django.db.models.deletion
import model_clone.mixin


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='ContentBlock',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField(default=True, help_text='Uncheck to hide this.')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('mod_date', models.DateTimeField(auto_now=True, verbose_name='Last Modified')),
                ('position', models.PositiveIntegerField(default=0, help_text='Set a custom ordering. Lower numbers appear first.')),
                ('css_class', models.CharField(blank=True, max_length=256)),
                ('draft', models.BooleanField(blank=True, default=False)),
                ('saved', models.BooleanField(blank=True, default=False)),
            ],
            options={
                'ordering': ['position'],
                'abstract': False,
            },
            bases=(model_clone.mixin.CloneMixin, models.Model),
        ),
        migrations.CreateModel(
            name='ContentBlockTemplate',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('visible', models.BooleanField(default=True, help_text='Uncheck to hide this.')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('mod_date', models.DateTimeField(auto_now=True, verbose_name='Last Modified')),
                ('position', models.PositiveIntegerField(default=0, help_text='Set a custom ordering. Lower numbers appear first.')),
                ('name', models.CharField(max_length=256, unique=True)),
                ('template_filename', models.CharField(blank=True, max_length=256)),
                ('no_cache', models.BooleanField(default=False, help_text='Disable caching for content blocks created with this template.')),
            ],
            options={
                'ordering': ['position'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContentBlockTemplateField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('position', models.PositiveIntegerField(default=0, help_text='Set a custom ordering. Lower numbers appear first.')),
                ('field_type', models.CharField(choices=[('TextField', 'Text Field'), ('ContentField', 'Content Field'), ('ImageField', 'Image Field'), ('VideoField', 'Video Field'), ('FileField', 'File Field'), ('EmbeddedVideoField', 'Embedded Video Field'), ('NestedField', 'Nested Field'), ('ModelChoiceField', 'Model Choice Field'), ('ChoiceField', 'Choice Field'), ('CheckboxField', 'Checkbox Field')], max_length=256)),
                ('key', models.SlugField(help_text='Must be unique to this content block template. Lowercase letters, numbers and underscores only.', max_length=256, validators=[django.core.validators.RegexValidator('[a-z0-9_]+', 'Lowercase letters, numbers and underscores only.')])),
                ('help_text', models.TextField(blank=True)),
                ('required', models.BooleanField(blank=True, default=False)),
                ('css_class', models.CharField(blank=True, help_text='Set a custom CSS class for this field in the editor.', max_length=256)),
                ('min_num', models.PositiveIntegerField(default=0, help_text='The minimum number of nested blocks allowed.')),
                ('max_num', models.PositiveIntegerField(default=99, help_text='The maximum number of nested blocks allowed.')),
                ('choices', models.TextField(blank=True)),
                ('content_block_template', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_block_template_fields', to='content_blocks.contentblocktemplate')),
                ('model_choice_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
                ('nested_templates', models.ManyToManyField(blank=True, help_text='Choose the content block templates that can be used in this nested field.', to='content_blocks.contentblocktemplate')),
            ],
            options={
                'ordering': ['position'],
                'abstract': False,
                'unique_together': {('key', 'content_block_template')},
            },
        ),
        migrations.CreateModel(
            name='ContentBlockField',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('field_type', models.CharField(max_length=256)),
                ('text', models.CharField(blank=True, max_length=256)),
                ('content', models.TextField(blank=True)),
                ('checkbox', models.BooleanField(blank=True, default=False)),
                ('image', content_blocks.fields.SVGAndImageField(blank=True, storage=content_blocks.models.image_storage, upload_to='content-blocks/images')),
                ('file', models.FileField(blank=True, storage=content_blocks.models.file_storage, upload_to='content-blocks/files')),
                ('choice', models.CharField(blank=True, max_length=256)),
                ('video', content_blocks.fields.VideoField(blank=True, storage=content_blocks.models.video_storage, upload_to='content-blocks/videos')),
                ('embedded_video', models.CharField(blank=True, max_length=256)),
                ('model_choice_object_id', models.PositiveIntegerField(blank=True, null=True)),
                ('content_block', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='content_block_fields', to='content_blocks.contentblock')),
                ('model_choice_content_type', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to='contenttypes.contenttype')),
                ('template_field', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='fields', to='content_blocks.contentblocktemplatefield')),
            ],
            options={
                'ordering': ['template_field__position'],
            },
            bases=(models.Model, model_clone.mixin.CloneMixin),
        ),
        migrations.CreateModel(
            name='ContentBlockCollection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('mod_date', models.DateTimeField(auto_now=True, verbose_name='Last Modified')),
                ('name', models.CharField(blank=True, help_text='For identification purposes only.', max_length=256)),
                ('slug', models.SlugField(unique=True)),
                ('content_blocks', models.ManyToManyField(to='content_blocks.contentblock')),
            ],
            options={
                'ordering': ['-create_date'],
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='ContentBlockAvailability',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('create_date', models.DateTimeField(auto_now_add=True, verbose_name='Creation Date')),
                ('mod_date', models.DateTimeField(auto_now=True, verbose_name='Last Modified')),
                ('content_block_templates', models.ManyToManyField(to='content_blocks.contentblocktemplate')),
                ('content_type', models.OneToOneField(null=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
            options={
                'verbose_name_plural': 'Content block availabilities',
            },
        ),
        migrations.AddField(
            model_name='contentblock',
            name='content_block_template',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='content_blocks.contentblocktemplate'),
        ),
        migrations.AddField(
            model_name='contentblock',
            name='parent',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='content_blocks', to='content_blocks.contentblockfield'),
        ),
        migrations.CreateModel(
            name='CheckboxField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='ChoiceField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='ContentField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='EmbeddedVideoField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='FileField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='ImageField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='ModelChoiceField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='NestedField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='TextField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
        migrations.CreateModel(
            name='VideoField',
            fields=[
            ],
            options={
                'proxy': True,
                'indexes': [],
                'constraints': [],
            },
            bases=('content_blocks.contentblockfield',),
        ),
    ]
