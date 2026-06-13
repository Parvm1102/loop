from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from greencredits.models import GreenCreditAccount
from greencredits.logic import seed_rewards

class Command(BaseCommand):
    help = 'Seed demo green credit accounts and rewards.'

    def handle(self, *args, **options):
        User = get_user_model()
        demo_users = [
            ('buyer1', 80),
            ('rahul', 50),
            ('seller1', 0),
            ('facility1', 0),
        ]
        for username, balance in demo_users:
            try:
                user = User.objects.get(username=username)
                account, _ = GreenCreditAccount.objects.get_or_create(user=user)
                account.balance = balance
                account.save()
                self.stdout.write(self.style.SUCCESS(f'Seeded {username} with {balance} credits'))
            except User.DoesNotExist:
                self.stdout.write(self.style.WARNING(f'User {username} not found'))

        seed_rewards()
        self.stdout.write(self.style.SUCCESS('Seeded rewards'))
