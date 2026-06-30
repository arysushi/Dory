"""
SyncSave — tracks spending, recommends savings, and auto-deposits spare change.

When your checking balance stays above a threshold you set, SyncSave quietly
moves a few cents into savings so progress happens without willpower.
"""

import uuid
from collections import defaultdict
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from .models import (
    AutoDeposit,
    Expense,
    ExpenseCategory,
    SavingsRecommendation,
    SpendingInsight,
)
from .storage import DEFAULT_DATA_PATH, load_data, save_data
from .tips import GENERAL_TIPS, tip_for_category


class SyncSave:
    """Personal savings coach with expense tracking and micro-deposits."""

    def __init__(self, data_path: Path = DEFAULT_DATA_PATH):
        self.data_path = data_path
        self._state = load_data(data_path)

    # ── configuration ──────────────────────────────────────────────

    @property
    def monthly_income(self) -> float:
        return self._state["monthly_income"]

    @monthly_income.setter
    def monthly_income(self, value: float) -> None:
        self._state["monthly_income"] = max(0.0, value)
        self._persist()

    @property
    def checking_balance(self) -> float:
        return self._state["checking_balance"]

    @checking_balance.setter
    def checking_balance(self, value: float) -> None:
        self._state["checking_balance"] = max(0.0, value)
        self._persist()

    @property
    def savings_balance(self) -> float:
        return self._state["savings_balance"]

    @property
    def min_balance_threshold(self) -> float:
        return self._state["min_balance_threshold"]

    @min_balance_threshold.setter
    def min_balance_threshold(self, value: float) -> None:
        self._state["min_balance_threshold"] = max(0.0, value)
        self._persist()

    @property
    def enrolled(self) -> bool:
        return self._state.get("enrolled", False)

    @property
    def daily_contribution_cents(self) -> int:
        return self._state.get("daily_contribution_cents", self._state["deposit_cents"])

    @daily_contribution_cents.setter
    def daily_contribution_cents(self, value: int) -> None:
        cents = max(1, min(int(value), 50000))
        self._state["daily_contribution_cents"] = cents
        self._state["deposit_cents"] = cents
        self._persist()

    @property
    def deposit_cents(self) -> int:
        return self.daily_contribution_cents

    @deposit_cents.setter
    def deposit_cents(self, value: int) -> None:
        self.daily_contribution_cents = value

    def configure(
        self,
        *,
        monthly_income: Optional[float] = None,
        min_balance_threshold: Optional[float] = None,
        deposit_cents: Optional[int] = None,
        daily_contribution_cents: Optional[int] = None,
    ) -> None:
        if monthly_income is not None:
            self.monthly_income = monthly_income
        if min_balance_threshold is not None:
            self.min_balance_threshold = min_balance_threshold
        cents = daily_contribution_cents if daily_contribution_cents is not None else deposit_cents
        if cents is not None:
            self.daily_contribution_cents = cents

    # ── expense tracking ─────────────────────────────────────────

    def track_expense(
        self,
        amount: float,
        category: ExpenseCategory | str,
        description: str = "",
    ) -> Expense:
        if isinstance(category, str):
            category = ExpenseCategory(category)

        expense = Expense(
            id=str(uuid.uuid4())[:8],
            amount=round(abs(amount), 2),
            category=category,
            description=description,
        )
        self._state["expenses"].append(expense.to_dict())
        self._state["checking_balance"] = max(
            0.0, self._state["checking_balance"] - expense.amount
        )
        self._persist()
        return expense

    def get_expenses(self, days: int = 30) -> list[Expense]:
        cutoff = datetime.now() - timedelta(days=days)
        result = []
        for raw in self._state["expenses"]:
            try:
                exp_date = datetime.fromisoformat(raw["date"])
            except ValueError:
                continue
            if exp_date >= cutoff:
                result.append(Expense.from_dict(raw))
        return sorted(result, key=lambda e: e.date, reverse=True)

    # ── spending habits ────────────────────────────────────────────

    def get_spending_habits(self, days: int = 30) -> list[SpendingInsight]:
        expenses = self.get_expenses(days)
        if not expenses:
            return []

        totals: dict[str, float] = defaultdict(float)
        for exp in expenses:
            totals[exp.category.value] += exp.amount

        grand_total = sum(totals.values())
        insights = []
        for cat, total in sorted(totals.items(), key=lambda x: -x[1]):
            pct = (total / grand_total) * 100 if grand_total else 0
            if pct > 25:
                trend = "high"
            elif pct > 10:
                trend = "moderate"
            else:
                trend = "low"
            insights.append(
                SpendingInsight(
                    category=cat,
                    total=round(total, 2),
                    percentage=round(pct, 1),
                    trend=trend,
                    advice=tip_for_category(cat, pct),
                )
            )
        return insights

    # ── savings recommendation ─────────────────────────────────────

    def get_savings_recommendation(self, days: int = 30) -> SavingsRecommendation:
        income = self.monthly_income
        expenses = self.get_expenses(days)
        total_spent = sum(e.amount for e in expenses)

        # Scale spending to monthly if tracking window is shorter
        scale = 30 / days if days > 0 else 1
        monthly_spent = total_spent * scale

        # 50/30/20: aim for 20% savings; adjust down if needs exceed 50%
        target_rate = 0.20
        if income > 0:
            needs_estimate = monthly_spent * 0.7  # rough needs share
            if needs_estimate / income > 0.50:
                target_rate = max(0.05, 0.20 - (needs_estimate / income - 0.50))

        recommended = round(income * target_rate, 2) if income > 0 else 0.0
        current_rate = (
            max(0.0, (income - monthly_spent) / income) if income > 0 else 0.0
        )
        gap = round(recommended - (income - monthly_spent), 2)

        breakdown = {
            "needs_estimate": round(monthly_spent * 0.5, 2),
            "wants_estimate": round(monthly_spent * 0.3, 2),
            "current_savings": round(max(0, income - monthly_spent), 2),
            "recommended_savings": recommended,
        }

        tips = self._build_personalized_tips(gap, current_rate, target_rate)

        return SavingsRecommendation(
            monthly_income=income,
            total_spent=round(monthly_spent, 2),
            recommended_monthly_savings=recommended,
            recommended_percentage=round(target_rate * 100, 1),
            current_savings_rate=round(current_rate * 100, 1),
            gap=gap,
            breakdown=breakdown,
            tips=tips,
        )

    def _build_personalized_tips(
        self, gap: float, current_rate: float, target_rate: float
    ) -> list[str]:
        tips = []
        if gap > 0:
            tips.append(
                f"You're ${gap:.2f}/month short of your savings goal. "
                f"Try cutting one discretionary category by 10%."
            )
        elif current_rate >= target_rate:
            tips.append(
                "You're meeting your savings target — great work! "
                "Consider bumping your goal by 1%."
            )

        habits = self.get_spending_habits()
        high = [h for h in habits if h.trend == "high"]
        for h in high[:2]:
            tips.append(h.advice)

        remaining = 4 - len(tips)
        tips.extend(GENERAL_TIPS[:remaining])
        return tips[:5]

    # ── onboarding & daily contribution ────────────────────────────

    def seed_linked_account_data(self) -> None:
        """Simulate linked Synchrony account spending for first-time analysis."""
        if self._state["expenses"]:
            return
        from datetime import datetime, timedelta

        samples = [
            (32.40, "food", "Trader Joe's"),
            (14.99, "subscriptions", "Streaming"),
            (67.20, "food", "Groceries"),
            (9.50, "food", "Coffee"),
            (45.00, "entertainment", "Dining out"),
            (120.00, "utilities", "Electric bill"),
            (28.00, "transport", "Gas"),
            (19.99, "shopping", "Amazon"),
            (38.50, "food", "Restaurant"),
            (12.00, "transport", "Rideshare"),
        ]
        base = datetime.now()
        for i, (amt, cat, desc) in enumerate(samples):
            exp = Expense(
                id=str(uuid.uuid4())[:8],
                amount=amt,
                category=ExpenseCategory(cat),
                description=desc,
                date=(base - timedelta(days=i % 28, hours=i)).isoformat(),
            )
            self._state["expenses"].append(exp.to_dict())
        self._persist()

    def suggest_daily_contribution(self) -> dict:
        """
        Analyze expenses and income to suggest a comfortable daily savings amount.
        """
        rec = self.get_savings_recommendation()
        habits = self.get_spending_habits()
        income = self.monthly_income
        monthly_spent = rec.total_spent

        if rec.recommended_monthly_savings > 0:
            daily = rec.recommended_monthly_savings / 30
        elif income > 0:
            daily = (income * 0.05) / 30
        else:
            daily = 0.35

        # Ease off if discretionary spending is heavy
        discretionary = sum(
            h.total for h in habits if h.category in ("entertainment", "shopping", "food")
        )
        if monthly_spent > 0 and discretionary / monthly_spent > 0.45:
            daily *= 0.7

        # Micro-savings: a few cents a day (25¢–$1.00)
        suggested_cents = max(25, min(int(round(daily * 100)), 100))
        suggested_daily = round(suggested_cents / 100, 2)
        monthly_projection = round(suggested_daily * 30, 2)
        yearly_projection = round(suggested_daily * 365, 2)

        return {
            "suggested_cents": suggested_cents,
            "suggested_daily": suggested_daily,
            "monthly_projection": monthly_projection,
            "yearly_projection": yearly_projection,
            "monthly_spending": monthly_spent,
            "recommended_monthly_savings": rec.recommended_monthly_savings,
            "top_categories": [h.to_dict() for h in habits[:3]],
            "explanation": (
                f"Based on your spending of ${monthly_spent:.2f}/month, "
                f"we suggest saving {suggested_cents}¢ per day — about "
                f"${monthly_projection:.2f}/month without feeling a pinch."
            ),
        }

    def enroll(self, daily_contribution_cents: int, min_balance_threshold: float) -> None:
        self.daily_contribution_cents = daily_contribution_cents
        self.min_balance_threshold = min_balance_threshold
        self._state["enrolled"] = True
        self._state["enrolled_at"] = datetime.now().isoformat()
        self._persist()

    def reset_enrollment(self) -> None:
        """Return user to onboarding without clearing savings history."""
        self._state["enrolled"] = False
        self._state["enrolled_at"] = None
        self._persist()

    def get_daily_deposits(self, days: int = 14) -> list[dict]:
        """Group auto-deposits by calendar day for the homepage feed."""
        by_day: dict[str, float] = defaultdict(float)
        for raw in self._state["auto_deposits"]:
            try:
                day = datetime.fromisoformat(raw["timestamp"]).strftime("%Y-%m-%d")
            except ValueError:
                continue
            by_day[day] += raw["amount"]

        result = []
        today = datetime.now().date()
        for i in range(days):
            d = today - timedelta(days=i)
            key = d.strftime("%Y-%m-%d")
            amount = round(by_day.get(key, 0.0), 2)
            result.append({
                "date": key,
                "label": "Today" if i == 0 else d.strftime("%a, %b %d"),
                "amount": amount,
                "deposited": amount > 0,
            })
        return result

    def get_home_summary(self) -> dict:
        daily = self.get_daily_deposits(14)
        today = daily[0] if daily else {"amount": 0, "deposited": False}
        streak = 0
        for day in daily:
            if day["deposited"]:
                streak += 1
            else:
                break

        return {
            "enrolled": self.enrolled,
            "savings_balance": self.savings_balance,
            "total_auto_saved": self._state["total_auto_saved"],
            "daily_contribution_cents": self.daily_contribution_cents,
            "daily_contribution": round(self.daily_contribution_cents / 100, 2),
            "min_balance_threshold": self.min_balance_threshold,
            "checking_balance": self.checking_balance,
            "today_deposit": today,
            "daily_feed": daily,
            "streak_days": streak,
            "can_deposit_today": (
                self.checking_balance > self.min_balance_threshold
                and not today["deposited"]
            ),
            "monthly_projection": round(self.daily_contribution_cents / 100 * 30, 2),
        }

    def get_onboarding_data(self) -> dict:
        self.seed_linked_account_data()
        suggestion = self.suggest_daily_contribution()
        habits = self.get_spending_habits()
        return {
            "monthly_income": self.monthly_income,
            "checking_balance": self.checking_balance,
            "spending_habits": [h.to_dict() for h in habits],
            "suggestion": suggestion,
        }


    def sync_save(self) -> Optional[AutoDeposit]:
        """
        Daily SyncSave: if checking balance exceeds threshold and no deposit
        yet today, move daily_contribution_cents into savings.
        """
        today_key = datetime.now().strftime("%Y-%m-%d")
        for raw in self._state["auto_deposits"]:
            try:
                day = datetime.fromisoformat(raw["timestamp"]).strftime("%Y-%m-%d")
                if day == today_key:
                    return None
            except ValueError:
                continue

        balance = self.checking_balance
        threshold = self.min_balance_threshold
        cents = self.daily_contribution_cents
        deposit_amount = round(cents / 100, 2)

        if balance <= threshold:
            return None
        if balance - deposit_amount < threshold:
            return None

        self._state["checking_balance"] = round(balance - deposit_amount, 2)
        self._state["savings_balance"] = round(
            self._state["savings_balance"] + deposit_amount, 2
        )
        self._state["total_auto_saved"] = round(
            self._state["total_auto_saved"] + deposit_amount, 2
        )

        record = AutoDeposit(
            amount=deposit_amount,
            timestamp=datetime.now().isoformat(),
            balance_before=balance,
            balance_after=self._state["checking_balance"],
        )
        self._state["auto_deposits"].append(record.to_dict())
        self._persist()
        return record

    def get_auto_deposit_history(self, limit: int = 20) -> list[AutoDeposit]:
        records = self._state["auto_deposits"][-limit:]
        return [AutoDeposit.from_dict(r) for r in reversed(records)]

    # ── dashboard summary ──────────────────────────────────────────

    def get_summary(self) -> dict:
        rec = self.get_savings_recommendation()
        habits = self.get_spending_habits()
        recent = self.get_expenses(7)

        return {
            "enrolled": self.enrolled,
            "checking_balance": self.checking_balance,
            "savings_balance": self.savings_balance,
            "total_auto_saved": self._state["total_auto_saved"],
            "min_balance_threshold": self.min_balance_threshold,
            "daily_contribution_cents": self.daily_contribution_cents,
            "deposit_cents": self.daily_contribution_cents,
            "monthly_income": self.monthly_income,
            "recommendation": rec.to_dict(),
            "spending_habits": [h.to_dict() for h in habits],
            "recent_expenses": [e.to_dict() for e in recent[:10]],
            "auto_deposits": [
                d.to_dict() for d in self.get_auto_deposit_history(10)
            ],
            "can_sync": self.checking_balance > self.min_balance_threshold,
        }

    def _persist(self) -> None:
        save_data(self._state, self.data_path)


def sync_save(
    checking_balance: float,
    min_balance_threshold: float,
    deposit_cents: int = 50,
    savings_balance: float = 0.0,
) -> dict:
    """
    Standalone SyncSave function for one-off micro-deposit checks.

    Returns a dict with whether a deposit occurred and updated balances.
    """
    deposit_amount = round(deposit_cents / 100, 2)
    result = {
        "deposited": False,
        "amount": 0.0,
        "checking_balance": checking_balance,
        "savings_balance": savings_balance,
        "message": "",
    }

    if checking_balance <= min_balance_threshold:
        result["message"] = (
            f"Balance ${checking_balance:.2f} is at or below your "
            f"${min_balance_threshold:.2f} threshold — no deposit."
        )
        return result

    if checking_balance - deposit_amount < min_balance_threshold:
        result["message"] = (
            "Deposit would drop balance below threshold — skipped."
        )
        return result

    result["deposited"] = True
    result["amount"] = deposit_amount
    result["checking_balance"] = round(checking_balance - deposit_amount, 2)
    result["savings_balance"] = round(savings_balance + deposit_amount, 2)
    result["message"] = (
        f"Deposited ${deposit_amount:.2f} into savings! "
        f"New checking: ${result['checking_balance']:.2f}, "
        f"savings: ${result['savings_balance']:.2f}."
    )
    return result
