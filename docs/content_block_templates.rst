Content Block Templates
=======================

:py:class:`ContentBlockTemplate`
--------------------------------

You can create :py:class:`ContentBlockTemplate` objects in the admin site.

.. py:class:: ContentBlockTemplate

    .. py:attribute:: name

        Unique name to identify the content block template with.

    .. py:attribute:: template_filename

        The file name of a template in the `content_blocks/content_blocks` template directory.  You would usually create this directory in your project's template directory as defined in your project settings. This template is used to render content blocks made with this ContentBlockTemplate.

        If this is not provided content blocks made from this template cannot be rendered. This may be suitable for nested content blocks.

    .. py:attribute:: no_cache

        Prevent this content block from being cached.  This can be useful if your template contains a template tag which provides content that shouldn't be cached.

:py:class:`ContentBlockTemplateField`
-------------------------------------

:py:class:`ContentBlockTemplateField` objects are created inline in the :py:class:`ContentBlockTemplate` admin change page. You can drag and drop to reorder the fields in the content block editor.

Most types of :py:class:`ContentBlockTemplateField` have the options shown here when adding them via the admin site. Some types have additional options detailed below in the relevant :ref:`ContentBlockField` section.

.. py:class:: ContentBlockTemplateField

    .. py:attribute:: field_type

        Choose the field type.  All types are detailed below.  Can't be changed once saved.

    .. py:attribute:: key

        The key is used when rendering template and is the key for the context provided by this field.

    .. py:attribute:: help_text

        Show some help text for this field in the content block editor.  Help text is shown as information tooltips the user can hover over to read.

    .. py:attribute:: required

        If checked this field cannot be left blank in the content block editor.

    .. py:attribute:: css_class

        The css class provided is added to the field wrapper in the content block editor. You can use this alongside some js to provide additional functionality for fields in the content block editor such as wysiwyg editors.

.. _ContentBlockField:

:py:class:`ContentBlockField`
-----------------------------

:py:class:`ContentBlockTemplateField` objects create :py:class:`ContentBlockField` objects.  The details of each type is given here as well as example usage in templates.

:py:class:`TextField`
^^^^^^^^^^^^^^^^^^^^^

Intended use is for single line text content.

.. py:class:: TextField

    .. py:property:: form_field

        :rtype: :py:class:`django.forms.CharField`

        The field used in the content block editor.

    .. py:property:: context_value

        :rtype: :py:class:`str`

        The context value in :py:attr:`ContentBlock.context`. To be used in templates.

.. code-block:: django
    :caption: Template Usage Example (``key = "text"``)

    <h2>{{ content_block.text }}</h2>

:py:class:`ContentField`
^^^^^^^^^^^^^^^^^^^^^^^^

Intended use is for multiline text content.

.. py:class:: ContentField

    .. py:property:: form_field

        :rtype: :py:class:`django.forms.CharField`

        :widget:
            :py:class:`django.forms.TextArea`

    .. py:property:: context_value

        :rtype: :py:class:`str`

.. code-block:: django
    :caption: Template Usage Example (``key = "content"``)

    {{ content_block.content|linebreaks }}

:py:class:`ImageField`
^^^^^^^^^^^^^^^^^^^^^^

A preview of the image is shown in the content block editor.

.. py:class:: ImageField

    .. py:property:: form_field

        :rtype: :py:class:`content_blocks.fields.SVGAndImageFieldFormField` a subclass of :py:class:`django.forms.ImageField` which also accepts svg files.

    .. py:property:: context_value

        :rtype: :py:class:`django.db.models.fields.files.ImageFieldFile`

.. code-block:: django
    :caption: Template Usage Example (``key = "image"``)

    <img src="{{ content_block.image.url }}" />

:py:class:`VideoField`
^^^^^^^^^^^^^^^^^^^^^^

A preview of the video is shown in the content block editor.

.. py:class:: VideoField

    .. py:property:: form_field

        :rtype: :py:class:`forms.FileField`

    .. py:property:: context_value

        :rtype: :py:class:`content_blocks.fields.FieldVideo` a subclass of :py:class:`django.db.models.fields.files.FieldFile` which provides the :py:attr:`file_extension` property.

.. code-block:: django
    :caption: Template Usage Example (``key = "video"``)

    <video>
        <source src="{{ content_block.video.url }}"
         type="video/{{ content_block.video.file_extension }}">
    </video>

:py:class:`FileField`
^^^^^^^^^^^^^^^^^^^^^

Intended for all files except image and video.

.. py:class:: FileField

    .. py:property:: form_field

        :rtype: :py:class:`forms.FileField`

    .. py:property:: context_value

        :rtype: :py:class:`django.db.models.fields.files.FieldFile`

.. code-block:: django
    :caption: Template Usage Example (``key = "file"``)

    <a href="{{ content_block.file.url }}">Download</a>

:py:class:`EmbeddedVideoField`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^^^

A preview of the embedded video is shown in the content block editor.  Supports YouTube, Vimeo and possibly others.

.. py:class:: EmbeddedVideoField

    .. py:property:: form_field

        :rtype: :py:class:`django.forms.CharField`

    .. py:property:: context_value

        :rtype: :py:class:`str`

.. code-block:: django
    :caption: Template Usage Example (``key = "embedded_video"``)

    <iframe src="{{ content_block.embedded_video }}" frameborder="0"
     allow="accelerometer; autoplay; clipboard-write; encrypted-media; gyroscope; picture-in-picture"
     webkitallowfullscreen mozallowfullscreen allowfullscreen></iframe>

:py:class:`NestedField`
^^^^^^^^^^^^^^^^^^^^^^^

Can be used to make things such as image galleries and menus. They function in a similar way to Django admin inlines but as the name implies they can be nested.

When adding a :py:class:`NestedField` you choose which :py:class:`ContentBlockTemplate` objects can be used to create nested content blocks.  You can reuse existing :py:class:`ContentBlockTemplate` objects or create new ones just for use with this :py:class:`NestedField`. If you create new ones then you might want to hide them from use as top level content blocks by creating a :ref:`ContentBlockAvailability <ContentBlockAvailability>`.

.. py:class:: NestedField

    .. py:property:: form_field

        :return: :py:class:`None`. Nested fields do not use a form field. They use a form which is appended to the content block form.

    .. py:property:: context_value

        :return: A :py:class:`QuerySet` of nested :py:class:`ContentBlock` objects.

The following additional options are available for :py:class:`ContentBlockTemplate`:

* :py:attr:`nested_templates` Choose which :py:class:`ContentBlockTemplate` can be used to create nested content blocks.

* :py:attr:`min_num` The minimum number of nested content blocks that can be created. The editor will prevent nested content blocks from being deleted if there are :py:attr:`min_num` or fewer. When adding a new content block this number of nested content blocks will be created, the first chosen :py:attr:`nested_templates` is used to create these initial nested content blocks.

* :py:attr:`max_num` The maximum number of nested content blocks that can be created. The editor will prevent nested content blocks from being created if there are :py:attr:`max_num` or more.

.. code-block:: django
    :caption: Template Usage Example (``key = "nested_content_blocks"``)

    {# If the nested content block template has a template_filename you can use render. #}

    {% for nested_content_block in nested_content_blocks %}
        {{ nested_content_block.render }}
    {% endfor %}

    {# Or you can reference the context of the nested content block. #}
    {# In this example our nested content block has a field with a key of "text" #}

    {% for nested_content_block in nested_content_blocks %}
        <h3>{{ nested_content_block.context.text }}</h3>
    {% endfor %}


:py:class:`ModelChoiceField`
^^^^^^^^^^^^^^^^^^^^^^^^^^^^

:py:class:`ModelChoiceField` let's us reference objects from other models in your project via the `Django contenttypes framework <https://docs.djangoproject.com/en/4.2/ref/contrib/contenttypes/>`_. When created in the admin site we choose the :py:attr:`model_choice_content_type`. When used in the content block editor the choices are ``model_choice.content_type.objects.all()``.

.. py:class:: ModelChoiceField

    .. py:property:: form_field

        :rtype: :py:class:`forms.ModelChoiceField`

    .. py:property:: context_value

        :return: The chosen object of the type given by :py:attr:`model_choice_content_type`.

The following additional options are available for :py:class:`ContentBlockTemplate`:

* :py:attr:`model_choice_content_type` Choose the :py:class:`ContentType` for the available choices.

.. code-block:: django
    :caption: Template Usage Example (``key = "model_choice"``)

    {# Here our related object has an attribute "name". #}

    <h2>{{ content_block.model_choice.name }}</h2>

    {# We can make related objects blocks when used in a NestedField. #}

    {% for nested_content_block in content_block.nested_content_blocks %}
        <h3>{{ nested_content_block.model_choice.name }}</h3>
    {% endfor %}

    {# When used with template tags we can make awesome things happen. #}
    {# Here we have a template tag that takes our object as an argument. #}

    {% load awesome_tags %}
    {% do_something_awesome content_block.model_choice %}

:py:class:`ChoiceField`
^^^^^^^^^^^^^^^^^^^^^^^

We can set a list of choices to choose from in the content block editor. Can be useful for providing style options via css classes.

.. py:class:: ChoiceField

    .. py:property:: form_field

        :rtype: :py:class:`forms.CharField`

    .. py:property:: context_value

        :rtype: :py:class:`str`

The following additional options are available for :py:class:`ContentBlockTemplate`:

* :py:attr:`choices` Set the available choices.

.. code-block:: django
    :caption: Template Usage Example (``key = "choice"``)

    <h2 class="{{ content_block.choice }}">Stylish by choice!</h2>

:py:class:`CheckboxField`
^^^^^^^^^^^^^^^^^^^^^^^^^

We can also add a checkbox for providing further customisation options.

.. py:class:: CheckboxField

    .. py:property:: form_field

        :rtype: :py:class:`forms.BooleanField`

    .. py:property:: context_value

        :rtype: :py:class:`bool`

.. code-block:: django
    :caption: Template Usage Example (``key = "checkbox"``)

    {% if content_block.checkbox %}
        <h3>Something</h3>
    {% else %}
        <h2>Something else!</h2>
    {% endif %}
