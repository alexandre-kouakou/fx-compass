from django.core.management.base import BaseCommand

from rates.services import refresh


class Command(BaseCommand):
    help = "Download all daily reference rates since HISTORY_START (safe to re-run)."

    def handle(self, *args, **opts):
        ecb, aed = refresh(full=True)
        for entry in (ecb, aed):
            if entry is None:
                continue
            status = "OK" if entry.ok else "FAILED"
            self.stdout.write(f"{entry.source}: {status} rows={entry.rows} latest={entry.latest_date} {entry.message}")
