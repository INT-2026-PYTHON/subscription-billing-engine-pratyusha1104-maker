"""
FixedAmountDiscount — e.g., flat ₹500 off.

CAPPING RULE: if the fixed amount exceeds the subtotal, return subtotal
(so the discounted total never goes below zero).
"""

from billing_engine.money import Money
from billing_engine.discounts.base import Discount, DiscountContext


class FixedAmountDiscount(Discount):
    def __init__(self, amount: Money) -> None:
        # TODO Day 1
        if not isinstance(amount, Money):
            raise TypeError("Amount must be a Money instance")
        if amount.is_negative():
            raise ValueError("Discount amount cannot be negative")
            
        self.amount = amount

    def apply(self, subtotal: Money, context: DiscountContext) -> Money:
        # TODO Day 1
        if self.amount.currency != subtotal.currency:
            raise ValueError("Discount and subtotal currency mismatch")
            
        return min(self.amount, subtotal)
        