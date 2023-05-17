from django.core.management import BaseCommand

from content_blocks.models import ContentBlockParentModel
from content_blocks.services.content_block import CacheServices


class Command(BaseCommand):
    help = "Update content blocks cache"

    def handle(self, *args, **options):
        verbosity = int(options["verbosity"])

        CacheServices.update_cache_all(ContentBlockParentModel)

        if verbosity > 0:
            self.stdout.write("Content blocks cache updated")  # pragma: no cover
