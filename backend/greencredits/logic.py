from greencredits.models import GreenCreditAccount, CreditTransaction, Reward

def award_credits(user, amount, type, description, reference_id=None):
    if not user:
        return
    account, _ = GreenCreditAccount.objects.get_or_create(user=user)
    account.balance += amount
    account.save()
    CreditTransaction.objects.create(
        account=account,
        amount=amount,
        type=type,
        description=description,
        reference_id=reference_id,
    )


# Default Rewards Store catalog. Kept here (not inside a management command) so
# both `seed_greencredits` and the boot-time `seed_demo` seed an identical,
# idempotent set — otherwise the Rewards Store renders empty.
#   (title, description, cost, icon)
DEFAULT_REWARDS = [
    ("₹50 Mobile Recharge", "Mobile top-up", 50, "📱"),
    ("₹100 Mobile Recharge", "Mobile top-up", 90, "📱"),
    ("Plant a Tree", "We plant a tree for you", 30, "🌳"),
    ("Free Coffee Voucher", "Enjoy a free coffee", 40, "☕"),
    ("₹200 Amazon Pay", "Amazon Pay balance", 150, "💳"),
    ("Exclusive Green Badge", "Profile badge", 10, "🏅"),
]


def seed_rewards():
    """Create the default Rewards Store catalog if missing. Idempotent — safe to
    call on every boot. Returns the number of rewards newly created."""
    created = 0
    for title, desc, cost, icon in DEFAULT_REWARDS:
        _, was_created = Reward.objects.get_or_create(
            title=title,
            defaults={
                "description": desc,
                "cost": cost,
                "icon": icon,
                "active": True,
            },
        )
        created += int(was_created)
    return created
