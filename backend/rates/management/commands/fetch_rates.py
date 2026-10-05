from django.core.management.base import BaseCommand

from rates.services import refresh


class Command(BaseCommand):
    help = "Fetch rates published since the last stored day, plus live AED."

    def handle(self, *args, **opts):
        ecb, aed = refresh()
        for entry in (ecb, aed):
            if entry is None:
                self.stdout.write("ecb: already up to date")
                continue
            status = "OK" if entry.ok else "FAILED"
            self.stdout.write(f"{entry.source}: {status} rows={entry.rows} latest={entry.latest_date} {entry.message}")
