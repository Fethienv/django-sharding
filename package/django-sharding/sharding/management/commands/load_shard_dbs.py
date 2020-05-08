from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Create fixatures file for databases and load it"
    def handle(self, *args, **options):
        try:
            pass
        except:
            raise CommandError("Something went wrong here.")