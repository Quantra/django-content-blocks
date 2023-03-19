# How to use content blocks

## Installation

Add the `content_blocks` app to `installed_apps`.

Add `path('content-blocks/', include('content_blocks.urls')),` to your base `urlpatterns`.

For every model you want to add content blocks to inherit from the abstract model `ContentBlockParentModel`.  E.g.

    from content_blocks.models import ContentBlockParentModel

    class MyModel(ContentBlockParentModel):
        my_field = models.TextField()

Then for each model admin subclass `ContentBlockModelAdmin` and add `'content_blocks_button'` to fields.

Run `python manage.py migrate`.

## Configuration

Create content block templates using the admin site.

To limit which content blocks are available to a model create a `ContentBlockAvailability` object via the admin site.  Set the `model` field to `app.Model` for this model e.g. `imperium.Page` then choose which content blocks you want to make available.  By default all content blocks are available, including nested blocks so this should always be set.

## Displaying content blocks

Use something similar to the following snippet in your template.

    {% for content_block in my_obj.content_blocks.visible %}
        {{ content_block.render }}
    {% endfor %}

## Drafts & Publishing

When editing content blocks you are working on a duplicate set of content blocks marked as draft.  Any changes you make will not be shown on the website until you publish them.

It is possible to save your progress without publishing such that you can leave the editor and return later.

It is also possible to reset the draft content blocks.  This will make them the same as the currently published content blocks.

## HTML Templates

HTML templates are stored in `content_blocks/content_blocks` within the `content_blocks` app templates directory.  When creating a content block template you need only provide the filename.

Templates can then be overridden by creating templates in the projects base templates directory under the same path.

Templates can also be overridden in the admin site by using `db_templates`.  Create a `Template` object via the admin site and set the `name` to the path fof the template file e.g. `content_blocks/content_blocks/my_template.html`.  Leave the content field blank and press Save and continue editing.  The content field is now populated with the file contents.  Any edits you make to the HTML here are not automatically written to the file.

It is possible to just have a database template without a file but the name must still be a path as before e.g. `content_blocks/content_blocks/my_template.html`.  Simply write the HTML in the content field.