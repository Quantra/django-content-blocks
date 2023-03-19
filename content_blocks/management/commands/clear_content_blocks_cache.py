from django.core.management import BaseCommand

from content_blocks.models import ContentBlock


class Command(BaseCommand):
    help = "Clear content blocks cache"

    def handle(self, *args, **options):
        verbosity = int(options["verbosity"])

        for content_block in ContentBlock.objects.all():
            content_block.clear_cache()

        if verbosity > 0:
            self.stdout.write("Content blocks cache cleared")  # pragma: no cover
