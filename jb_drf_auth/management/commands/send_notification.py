import json

from django.core.management.base import BaseCommand, CommandError

from jb_drf_auth.services.notification_dispatch import NotificationDispatchService


class Command(BaseCommand):
    help = "Send test notifications to one profile or broadcast to many."

    def add_arguments(self, parser):
        parser.add_argument("--profile-id", type=int, help="Target profile id (single send).")
        parser.add_argument(
            "--profile-ids",
            nargs="+",
            type=int,
            help="Optional list of target profile ids for broadcast.",
        )
        parser.add_argument(
            "--broadcast",
            action="store_true",
            help="Broadcast mode (all profiles or --profile-ids subset).",
        )
        parser.add_argument("--type", required=True, help="Notification type.")
        parser.add_argument("--title", required=True, help="Notification title.")
        parser.add_argument("--body", default="", help="Notification body.")
        parser.add_argument("--action-path", default=None, help="Optional action path.")
        parser.add_argument(
            "--channel",
            default="BOTH",
            choices=["IN_APP", "PUSH", "BOTH"],
            help="Dispatch channel.",
        )
        parser.add_argument(
            "--dedupe-key",
            default=None,
            help="Optional dedupe key for single send.",
        )
        parser.add_argument(
            "--dedupe-key-prefix",
            default=None,
            help="Optional dedupe prefix for broadcast.",
        )
        parser.add_argument(
            "--data",
            default="{}",
            help="Optional JSON payload for notification data.",
        )

    def handle(self, *args, **options):
        try:
            payload_data = json.loads(options["data"] or "{}")
        except json.JSONDecodeError as exc:
            raise CommandError(f"Invalid --data JSON: {exc}") from exc

        if not isinstance(payload_data, dict):
            raise CommandError("--data must be a JSON object.")

        is_broadcast = bool(options["broadcast"])
        profile_id = options.get("profile_id")
        profile_ids = options.get("profile_ids") or None

        if is_broadcast:
            result = NotificationDispatchService.broadcast(
                notification_type=options["type"],
                title=options["title"],
                body=options.get("body") or "",
                data=payload_data,
                action_path=options.get("action_path"),
                channel=options.get("channel"),
                dedupe_key_prefix=options.get("dedupe_key_prefix"),
                profile_ids=profile_ids,
            )
            self.stdout.write(
                self.style.SUCCESS(
                    f"Broadcast completed. sent={result['sent']} skipped={result['skipped']} total={result['total']}"
                )
            )
            return

        if not profile_id:
            raise CommandError("Use --profile-id for single send or --broadcast for broadcast mode.")

        notification = NotificationDispatchService.send_to_profile(
            profile_id=profile_id,
            notification_type=options["type"],
            title=options["title"],
            body=options.get("body") or "",
            data=payload_data,
            action_path=options.get("action_path"),
            channel=options.get("channel"),
            dedupe_key=options.get("dedupe_key"),
        )
        self.stdout.write(
            self.style.SUCCESS(f"Notification sent successfully. id={getattr(notification, 'id', None)}")
        )
