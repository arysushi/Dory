"""Data models for SyncCents."""

from dataclasses import dataclass, field, asdict
from datetime import datetime
from enum import Enum
from typing import Optional


class ExpenseCategory(str, Enum):
    HOUSING = "housing"
    FOOD = "food"
    TRANSPORT = "transport"
    ENTERTAINMENT = "entertainment"
    SHOPPING = "shopping"
    UTILITIES = "utilities"
    HEALTH = "health"
    SUBSCRIPTIONS = "subscriptions"
    OTHER = "other"


@dataclass
class Expense:
    amount: float
    category: ExpenseCategory
    description: str
    date: str = field(default_factory=lambda: datetime.now().isoformat())
    id: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "amount": self.amount,
            "category": self.category.value,
            "description": self.description,
            "date": self.date,
        }

    @classmethod
    def from_dict(cls, data: dict) -> "Expense":
        return cls(
            id=data.get("id"),
            amount=float(data["amount"]),
            category=ExpenseCategory(data["category"]),
            description=data["description"],
            date=data.get("date", datetime.now().isoformat()),
        )


@dataclass
class AutoDeposit:
    amount: float
    timestamp: str
    balance_before: float
    balance_after: float

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict) -> "AutoDeposit":
        return cls(**data)


@dataclass
class SavingsRecommendation:
    monthly_income: float
    total_spent: float
    recommended_monthly_savings: float
    recommended_percentage: float
    current_savings_rate: float
    gap: float
    breakdown: dict
    tips: list[str]

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SpendingInsight:
    category: str
    total: float
    percentage: float
    trend: str  # "high", "moderate", "low"
    advice: str

    def to_dict(self) -> dict:
        return asdict(self)
