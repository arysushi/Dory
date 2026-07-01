#!/usr/bin/env python3
"""Quick demo of sync-cents from the command line."""

from synccents import SyncCents, sync_cents

print("=== sync-cents Demo ===\n")

# Standalone one-off function
result = sync_cents(
    checking_balance=750.00,
    min_balance_threshold=500.00,
    deposit_cents=50,
    savings_balance=120.00,
)
print("One-off sync_cents():")
print(f"  {result['message']}\n")

# Full tracker
ss = SyncCents()
ss.configure(
    monthly_income=3500,
    min_balance_threshold=500,
    deposit_cents=75,
)
ss.checking_balance = 1200

ss.track_expense(45.00, "food", "Groceries")
ss.track_expense(12.50, "food", "Coffee")
ss.track_expense(89.00, "entertainment", "Concert tickets")
ss.track_expense(15.99, "subscriptions", "Streaming")

print(f"Checking: ${ss.checking_balance:.2f}")
print(f"Savings:  ${ss.savings_balance:.2f}\n")

rec = ss.get_savings_recommendation()
print(f"Recommended monthly savings: ${rec.recommended_monthly_savings:.2f} ({rec.recommended_percentage}%)")
print(f"Current savings rate: {rec.current_savings_rate}%")
print(f"Gap: ${rec.gap:.2f}\n")

print("Spending habits:")
for h in ss.get_spending_habits():
    print(f"  {h.category}: ${h.total:.2f} ({h.percentage}%) — {h.trend}")

print("\nTips:")
for tip in rec.tips:
    print(f"  • {tip}")

deposit = ss.sync_cents()
if deposit:
    print(f"\nAuto-deposited ${deposit.amount:.2f}!")
    print(f"Checking now: ${ss.checking_balance:.2f}, Savings: ${ss.savings_balance:.2f}")
else:
    print("\nNo auto-deposit (balance below threshold).")
