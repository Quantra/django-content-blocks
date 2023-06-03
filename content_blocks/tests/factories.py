"""
Test Factories
"""
import json

import factory
from django.contrib.contenttypes.models import ContentType
from django.contrib.sites.models import Site
from factory.django import DjangoModelFactory
from faker import Faker

from content_blocks.models import (
    ContentBlock,
    ContentBlockAvailability,
    ContentBlockCollection,
    ContentBlockField,
    ContentBlockFields,
    ContentBlockTemplate,
    ContentBlockTemplateField,
)
from example.pages.models import Page, PageSite, PageSites

faker = Faker()


class SiteFactory(DjangoModelFactory):
    domain = factory.Sequence(lambda n: f"{faker.domain_word()}{n}.{faker.tld()}")
    name = factory.Faker("text", max_nb_chars=50)

    class Meta:
        model = Site


class PageFactory(DjangoModelFactory):
    slug = factory.Faker("slug")

    class Meta:
        model = Page


class PageSitesFactory(DjangoModelFactory):
    slug = factory.Faker("slug")

    class Meta:
        model = PageSites


class PageSiteFactory(DjangoModelFactory):
    slug = factory.Faker("slug")

    class Meta:
        model = PageSite


class ContentBlockTemplateFactory(DjangoModelFactory):
    name = factory.Sequence(lambda n: f"Content Block Template {n}")

    class Meta:
        model = ContentBlockTemplate


class ContentBlockTemplateFieldFactory(DjangoModelFactory):
    content_block_template = factory.SubFactory(ContentBlockTemplateFactory)

    field_type = ContentBlockFields.TEXT_FIELD

    key = field_type.lower().replace(" ", "_")

    choices = json.dumps([["choice_1", "Choice 1"], ["choice_2", "Choice 2"]])

    class Meta:
        model = ContentBlockTemplateField


class NestedContentBlockTemplateFieldFactory(ContentBlockTemplateFieldFactory):
    field_type = ContentBlockFields.NESTED_FIELD
    key = field_type.lower().replace(" ", "_")

    @factory.post_generation
    def nested_templates(self, create, extracted, **kwargs):
        if not create:
            # Simple build, do nothing.
            return

        if extracted:
            # A list of groups were passed in, use them
            for content_block_template in extracted:
                self.nested_templates.add(content_block_template)


class ImageContentBlockTemplateFieldFactory(ContentBlockTemplateFieldFactory):
    field_type = ContentBlockFields.IMAGE_FIELD
    key = field_type.lower().replace(" ", "_")


class FileContentBlockTemplateFieldFactory(ContentBlockTemplateFieldFactory):
    field_type = ContentBlockFields.FILE_FIELD
    key = field_type.lower().replace(" ", "_")


class VideoContentBlockTemplateFieldFactory(ContentBlockTemplateFieldFactory):
    field_type = ContentBlockFields.VIDEO_FIELD
    key = field_type.lower().replace(" ", "_")


class ContentBlockFactory(DjangoModelFactory):
    content_block_template = factory.SubFactory(ContentBlockTemplateFactory)

    class Meta:
        model = ContentBlock


class ContentBlockFieldFactory(DjangoModelFactory):
    template_field = factory.SubFactory(ContentBlockTemplateFieldFactory)
    content_block = factory.SubFactory(ContentBlockFactory)

    field_type = factory.SelfAttribute("template_field.field_type")

    class Meta:
        model = ContentBlockField


class NestedContentBlockFieldFactory(ContentBlockFieldFactory):
    template_field = factory.SubFactory(NestedContentBlockTemplateFieldFactory)


class ImageContentBlockFieldFactory(ContentBlockFieldFactory):
    template_field = factory.SubFactory(ImageContentBlockTemplateFieldFactory)


class PopulatedImageContentBlockFieldFactory(ImageContentBlockFieldFactory):
    image = factory.django.ImageField(width=300, height=300)


class FileContentBlockFieldFactory(ContentBlockFieldFactory):
    template_field = factory.SubFactory(FileContentBlockTemplateFieldFactory)


class PopulatedFileContentBlockFieldFactory(FileContentBlockFieldFactory):
    file = factory.django.FileField(
        filename=factory.Faker("file_name", extension="pdf")
    )


class VideoContentBlockFieldFactory(ContentBlockFieldFactory):
    template_field = factory.SubFactory(VideoContentBlockTemplateFieldFactory)


class PopulatedVideoContentBlockFieldFactory(VideoContentBlockFieldFactory):
    video = factory.django.FileField(
        filename=factory.Faker("file_name", extension="mp4")
    )


class ContentBlockCollectionFactory(DjangoModelFactory):
    slug = factory.Faker("slug")

    class Meta:
        model = ContentBlockCollection


class ContentTypeFactory(DjangoModelFactory):
    class Meta:
        model = ContentType


class ContentBlockAvailabilityFactory(DjangoModelFactory):
    content_type = factory.SubFactory(ContentTypeFactory)

    class Meta:
        model = ContentBlockAvailability


#  DB Templates Factories

try:
    from dbtemplates.models import Template

    class TemplateFactory(DjangoModelFactory):
        name = factory.Sequence(lambda n: f"db_template_{n}.html")

        class Meta:
            model = Template

except RuntimeError:
    pass
