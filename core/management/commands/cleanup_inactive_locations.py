from django.core.management.base import BaseCommand
from core.utils import cleanup_inactive_locations

class Command(BaseCommand):
    help = 'Removes ActiveUser and ActiveCustomer records that have not been updated for more than 5 minutes.'

    def add_arguments(self, parser):
        parser.add_argument(
            '--minutes',
            type=int,
            default=5,
            help='Number of minutes of inactivity before deleting record (default: 5).'
        )

    def handle(self, *args, **options):
        minutes = options['minutes']
        deleted_users, deleted_customers = cleanup_inactive_locations(minutes=minutes)
        self.stdout.write(
            self.style.SUCCESS(
                f"Successfully cleaned up inactive locations (> {minutes} mins old): "
                f"{deleted_users} ActiveUsers and {deleted_customers} ActiveCustomers removed."
            )
        )
