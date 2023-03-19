from django.core.management import BaseCommand

from content_blocks.models import ContentBlock


class Command(BaseCommand):
    help = "Update content blocks cache"

    def handle(self, *args, **options):
        verbosity = int(options["verbosity"])

        for content_block in ContentBlock.objects.all():
            content_block.update_cache()

        if verbosity > 0:
            self.stdout.write("Content blocks cache updated")  # pragma: no cover
