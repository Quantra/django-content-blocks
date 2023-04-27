# Generated by Django 4.2 on 2023-04-27 12:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('content_blocks', '0002_alter_contentblock_css_class_and_more'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='contentblocktemplatefield',
            unique_together=set(),
        ),
        migrations.AlterField(
            model_name='contentblocktemplatefield',
            name='field_type',
            field=models.CharField(choices=[('TextField', 'Text Field'), ('ContentField', 'Content Field'), ('ImageField', 'Image Field'), ('NestedField', 'Nested Field'), ('CheckboxField', 'Checkbox Field'), ('ChoiceField', 'Choice Field'), ('ModelChoiceField', 'Model Choice Field'), ('FileField', 'File Field'), ('VideoField', 'Video Field'), ('EmbeddedVideoField', 'Embedded Video Field')], max_length=32),
        ),
        migrations.AddConstraint(
            model_name='contentblocktemplatefield',
            constraint=models.UniqueConstraint(fields=('key', 'content_block_template'), name='unique_key_content_block_template'),
        ),
    ]
