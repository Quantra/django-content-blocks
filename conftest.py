"""
Content blocks conf test.
Load factories for use in all tests.
"""
import itertools

import pytest
from django.core import serializers
from faker import Faker
from PIL import Image
from pytest_factoryboy import register

from content_blocks.cache import cache
from content_blocks.conf import settings
from content_blocks.tests.factories import (
    ContentBlockAvailabilityFactory,
    ContentBlockCollectionFactory,
    ContentBlockFactory,
    ContentBlockFieldFactory,
    ContentBlockTemplateFactory,
    ContentBlockTemplateFieldFactory,
    ContentTypeFactory,
    FileContentBlockFieldFactory,
    FileContentBlockTemplateFieldFactory,
    ImageContentBlockFieldFactory,
    ImageContentBlockTemplateFieldFactory,
    NestedContentBlockFieldFactory,
    NestedContentBlockTemplateFieldFactory,
    PageFactory,
    PageSiteFactory,
    PageSitesFactory,
    PopulatedFileContentBlockFieldFactory,
    PopulatedImageContentBlockFieldFactory,
    PopulatedVideoContentBlockFieldFactory,
    SiteFactory,
    VideoContentBlockFieldFactory,
    VideoContentBlockTemplateFieldFactory,
)

register(SiteFactory)
register(PageFactory)
register(PageSiteFactory)
register(PageSitesFactory)

register(FileContentBlockTemplateFieldFactory)
register(VideoContentBlockTemplateFieldFactory)
register(ImageContentBlockTemplateFieldFactory)
register(NestedContentBlockTemplateFieldFactory)
register(ContentBlockTemplateFactory)
register(ContentBlockTemplateFieldFactory)

register(PopulatedVideoContentBlockFieldFactory)
register(VideoContentBlockFieldFactory)
register(PopulatedFileContentBlockFieldFactory)
register(FileContentBlockFieldFactory)
register(PopulatedImageContentBlockFieldFactory)
register(ImageContentBlockFieldFactory)
register(NestedContentBlockFieldFactory)
register(ContentBlockFactory)
register(ContentBlockFieldFactory)

register(ContentTypeFactory)
register(ContentBlockAvailabilityFactory)

register(ContentBlockCollectionFactory)

try:
    from content_blocks.tests.factories import TemplateFactory

    register(TemplateFactory)
except ImportError:

    @pytest.fixture
    def template_factory():
        pass


faker = Faker()


@pytest.fixture(autouse=True)
def reset_cache():
    """
    Clear the cache between every test.
    """
    yield

    assert (
        settings.CACHES[settings.CONTENT_BLOCKS_CACHE]["BACKEND"]
        == "django.core.cache.backends.locmem.LocMemCache"
    )
    cache.clear()


@pytest.fixture(autouse=True)
def use_tmp_templates_dir(settings, tmp_path_factory):
    """
    Add the temporary templates dir to templates settings.
    """
    tmp_path_factory.mktemp("tmp-templates")

    loaders = [
        "dbtemplates.loader.Loader",
        "django.template.loaders.filesystem.Loader",
        "django.template.loaders.app_directories.Loader",
    ]

    if "dbtemplates" not in settings.INSTALLED_APPS:
        loaders.remove("dbtemplates.loader.Loader")

    settings.TEMPLATES = [
        {
            "BACKEND": "django.template.backends.django.DjangoTemplates",
            "DIRS": [
                tmp_path_factory.getbasetemp() / "tmp-templates",
                settings.BASE_DIR / "example" / "templates",
            ],
            "OPTIONS": {
                "context_processors": [
                    "django.template.context_processors.debug",
                    "django.template.context_processors.request",
                    "django.contrib.auth.context_processors.auth",
                    "django.contrib.messages.context_processors.messages",
                ],
                "loaders": loaders,
            },
        },
    ]


@pytest.fixture(autouse=True)
def use_tmp_media_root(settings, tmp_path_factory):
    tmp_path_factory.mktemp("tmp-media")

    settings.MEDIA_ROOT = tmp_path_factory.getbasetemp() / "tmp-media"


@pytest.fixture
def text_template(tmp_path_factory):
    """
    Text template for text content blocks.
    """
    template_content = "{{ content_block.textfield }}"
    template = (
        tmp_path_factory.getbasetemp()
        / "tmp-templates/content_blocks/content_blocks/_test_text.html"
    )
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(template_content)
    return template


@pytest.fixture
def nested_template(tmp_path_factory):
    """
    Nested template for nested content blocks.
    """
    template_content = "{% for b in content_block.nestedfield %}{{ b.context.textfield }}\n{% endfor %}"
    template = (
        tmp_path_factory.getbasetemp()
        / "tmp-templates/content_blocks/content_blocks/_test_nested.html"
    )
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(template_content)
    return template


@pytest.fixture
def model_choice_template(tmp_path_factory):
    """
    Model choice html template
    """
    template_content = "{{ content_block.modelchoicefield }}"
    template = (
        tmp_path_factory.getbasetemp()
        / "tmp-templates/content_blocks/content_blocks/_test_model_choice.html"
    )
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(template_content)
    return template


@pytest.fixture
def model_multiple_choice_template(tmp_path_factory):
    """
    Model multiple choice html template
    """
    template_content = (
        "{% for c in content_block.modelmultiplechoicefield.all %}{{ c }}{% endfor %}"
    )
    template = (
        tmp_path_factory.getbasetemp()
        / "tmp-templates/content_blocks/content_blocks/_test_model_multiple_choice.html"
    )
    template.parent.mkdir(parents=True, exist_ok=True)
    template.write_text(template_content)
    return template


@pytest.fixture
def text_content_block_template(content_block_template_factory, text_template):
    return content_block_template_factory.create(template_filename=text_template.name)


@pytest.fixture
def text_content_block(
    content_block_factory,
    text_content_block_template,
    content_block_field_factory,
):
    """
    Returns a content block with text field all set up with template so it can be rendered.
    """
    content_block = content_block_factory.create(
        content_block_template=text_content_block_template, draft=False
    )
    content_block_field_factory.create(
        text=faker.text(256), content_block=content_block
    )
    return content_block


@pytest.fixture
def text_content_blocks(
    request,
    text_content_block_template,
    content_block_factory,
    content_block_field_factory,
):
    text_content_blocks = []
    for i in range(request.param.get("num", 10)):
        content_block = content_block_factory.create(
            content_block_template=text_content_block_template, draft=False
        )
        content_block_field_factory.create(
            text=faker.text(256), content_block=content_block
        )
        text_content_blocks.append(content_block)

    return text_content_blocks


@pytest.fixture
def nested_content_block(
    nested_content_block_field_factory,
    content_block_factory,
    content_block_field_factory,
    nested_template,
    text_template,
    content_block_template_factory,
):
    # Create parent content block
    content_block_template = content_block_template_factory.create(
        template_filename=nested_template.name
    )
    content_block = content_block_factory.create(
        content_block_template=content_block_template, saved=True
    )
    nested_field = nested_content_block_field_factory.create(
        content_block=content_block
    )

    # Create a child content block
    nested_content_block_template = content_block_template_factory.create(
        template_filename=text_template.name
    )
    nested_content_block = content_block_factory.create(
        content_block_template=nested_content_block_template,
        parent=nested_field,
        saved=True,
    )
    content_block_field_factory.create(
        text=faker.text(256),
        content_block=nested_content_block,
    )
    return content_block, nested_content_block


@pytest.fixture
def svg_file(tmp_path_factory):
    """
    SVG file
    """
    svg_content = (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        "<!DOCTYPE svg>\n"
        '<svg xmlns="http://www.w3.org/2000/svg"\n'
        '      width="304" height="290">\n'
        '   <path d="M2,111 h300 l-242.7,176.3 92.7,-285.3 92.7,285.3 z" \n'
        '      style="fill:#FB2;stroke:#BBB;stroke-width:15;stroke-linejoin:round"/>\n'
        "</svg>\n"
    )

    svg = tmp_path_factory.getbasetemp() / "tmp-svgs/_test_svg.svg"
    svg.parent.mkdir(parents=True, exist_ok=True)
    svg.write_text(svg_content)
    return svg


@pytest.fixture
def text_file(tmp_path_factory):
    """
    Text file
    """
    text_content = faker.text()

    text = tmp_path_factory.getbasetemp() / "tmp-texts/_test_text.txt"
    text.parent.mkdir(parents=True, exist_ok=True)
    text.write_text(text_content)
    return text


@pytest.fixture
def png_file(tmp_path_factory):
    """
    Image file
    """
    image_content = Image.new("RGBA", (64, 64), color=(155, 0, 0))

    image = tmp_path_factory.getbasetemp() / "tmp-pngs/_text_png.png"
    image.parent.mkdir(parents=True, exist_ok=True)
    image_content.save(image)

    return image


@pytest.fixture
def cbt_import_export_objects(
    content_block_template,
    content_block_template_field_factory,
    content_block_factory,
    content_block_field_factory,
):
    """
    Create ContentBlockTemplate object with a ContentBlockTemplateField
    Create an associated ContentBlock and ContentBlockField
    :return: Tuple of objects created
    """
    content_block_template_field = content_block_template_field_factory.create(
        content_block_template=content_block_template
    )

    content_block = content_block_factory.create(
        content_block_template=content_block_template
    )
    content_block_field = content_block_field_factory.create(
        content_block=content_block,
        template_field=content_block_template_field,
    )

    return (
        content_block_template,
        content_block_template_field,
        content_block,
        content_block_field,
    )


@pytest.fixture
def cbt_import_export_json(cbt_import_export_objects):
    """
    :return: json string which matches the above cbt_import_export objects
    """
    content_block_template = cbt_import_export_objects[0]
    ContentBlockTemplate = type(content_block_template)

    content_block_template_field = cbt_import_export_objects[1]
    ContentBlockTemplateField = type(content_block_template_field)

    json_string = serializers.serialize(
        "json",
        itertools.chain(
            ContentBlockTemplate.objects.all(), ContentBlockTemplateField.objects.all()
        ),
    )
    return json_string


@pytest.fixture
def cbt_import_export_json_file(tmp_path_factory, cbt_import_export_json):
    """
    :return: The json from cbt_import_export_json in a temporary file.
    """
    json_file = tmp_path_factory.getbasetemp() / "tmp-exports/_export.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(cbt_import_export_json)
    return json_file


@pytest.fixture
def cbt_import_export_bad_json(content_block):
    """
    The json contains a ContentBlock instead of ContentBlockTemplate and ContentBlockTemplateField
    """
    ContentBlock = type(content_block)
    json_string = serializers.serialize("json", ContentBlock.objects.all())
    return json_string


@pytest.fixture
def cbt_import_export_bad_json_file(tmp_path_factory, cbt_import_export_bad_json):
    json_file = tmp_path_factory.getbasetemp() / "tmp-exports/_export_bad.json"
    json_file.parent.mkdir(parents=True, exist_ok=True)
    json_file.write_text(cbt_import_export_bad_json)
    return json_file
