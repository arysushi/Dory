"""Saving education tips based on spending patterns."""

CATEGORY_TIPS = {
    "food": "Try meal prepping on Sundays — it can cut dining-out costs by 30–40%.",
    "entertainment": "Set a weekly fun-money cap. Free activities (parks, libraries) count too.",
    "shopping": "Use the 24-hour rule: wait a day before non-essential purchases.",
    "subscriptions": "Audit subscriptions monthly — cancel anything you haven't used in 30 days.",
    "transport": "Combine errands into one trip or try carpooling to reduce fuel costs.",
    "housing": "Renegotiate rent or refinance if rates have dropped since you signed.",
    "utilities": "Lower your thermostat 2°F in winter — small change, real savings.",
    "health": "Use generic medications and in-network providers when possible.",
    "other": "Track every dollar for two weeks — awareness alone often reduces spending 10%.",
}

GENERAL_TIPS = [
    "Pay yourself first: move savings to a separate account on payday, before spending.",
    "The 50/30/20 rule works well — 50% needs, 30% wants, 20% savings.",
    "Micro-savings add up: even $0.50/day is $182/year without feeling the pinch.",
    "Build a $500 emergency fund before aggressive investing — it prevents debt spirals.",
    "Round up purchases mentally and sweep the difference into savings.",
    "Automate savings so you don't have to rely on willpower every month.",
]


def tip_for_category(category: str, percentage: float) -> str:
    base = CATEGORY_TIPS.get(category, CATEGORY_TIPS["other"])
    if percentage > 30:
        return f"This category is {percentage:.0f}% of spending — worth trimming. {base}"
    if percentage > 15:
        return f"Moderate share ({percentage:.0f}%). {base}"
    return f"Well managed at {percentage:.0f}%. Keep it up!"
