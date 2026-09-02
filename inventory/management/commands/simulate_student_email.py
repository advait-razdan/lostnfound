"""Simulate an incoming student "lost item" email without a real mailbox.

Creates a PENDING StudentLostItem exactly as check_emails would, attaches any
given images, and sends the same acknowledgment email — so the full workflow
(submission → approval queue → approve/reject → broadcast) can be tested locally.

Example:
    python manage.py simulate_student_email \
        --from "Priya Sharma <psharma@tisb.ac.in>" \
        --subject "Lost blue Hydroflask water bottle" \
        --body "I left it in the science block on Tuesday. It has a dented lid." \
        --image /path/to/photo.jpg
"""

import hashlib
import os

from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandError
from django.utils import timezone

from email.utils import parseaddr

from inventory.models import StudentLostItem, StudentLostItemImage


class Command(BaseCommand):
    help = "Create a PENDING StudentLostItem as if a student had emailed it in."

    def add_arguments(self, parser):
        parser.add_argument(
            "--from", dest="from_addr", required=True,
            help='Sender, e.g. "Priya Sharma <psharma@tisb.ac.in>" or just the address.',
        )
        parser.add_argument("--subject", required=True, help="Email subject → item title.")
        parser.add_argument("--body", default="", help="Email body → item description.")
        parser.add_argument(
            "--image", action="append", default=[], metavar="PATH",
            help="Path to an image to attach. Repeatable.",
        )

    def handle(self, *args, **options):
        display_name, from_email = parseaddr(options["from_addr"])
        from_email = (from_email or "").strip().lower()
        if not from_email:
            raise CommandError("Could not parse an email address from --from.")

        title = options["subject"].strip()[:200] or "Untitled lost item submission"
        body = options["body"].strip() or "No description was provided by the student in the email body."

        # Deterministic fake Message-ID so re-running with the same input dedups.
        source_message_id = "sim:" + hashlib.sha256(
            f"{from_email}|{title}|{body}".encode()
        ).hexdigest()[:64]

        if StudentLostItem.objects.filter(source_message_id=source_message_id).exists():
            raise CommandError(
                "A submission with identical sender/subject/body already exists "
                "(deduplicated). Change the subject or body to create a new one."
            )

        item = StudentLostItem.objects.create(
            title=title,
            description=body,
            email_subject=options["subject"].strip()[:500],
            email_from=from_email,
            submitter_display_name=display_name.strip(),
            source_message_id=source_message_id,
        )

        for path in options["image"]:
            if not os.path.exists(path):
                self.stderr.write(self.style.WARNING(f"Image not found, skipping: {path}"))
                continue
            with open(path, "rb") as fh:
                StudentLostItemImage.objects.create(
                    student_item=item,
                    image=ContentFile(fh.read(), name=os.path.basename(path)),
                )

        # Reuse the real acknowledgment email path so it is faithful to production.
        from inventory.management.commands.check_emails import Command as CheckEmailsCommand
        CheckEmailsCommand()._send_acknowledgment(item, oversized=False)

        # send_system_email() dispatches on a daemon thread that would be killed
        # when this CLI process exits before the .eml is flushed. Wait for it.
        import threading
        main = threading.main_thread()
        for t in threading.enumerate():
            if t is not main:
                t.join(timeout=10)

        self.stdout.write(self.style.SUCCESS(
            f"Created StudentLostItem #{item.pk} '{item.title}' (PENDING) from {from_email}. "
            f"Acknowledgment email queued. Review it at /staff/approval-queue/."
        ))
