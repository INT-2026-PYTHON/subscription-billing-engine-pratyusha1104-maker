"""
VATCalculator — single-rate VAT (e.g. 19% in Germany).
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class VATCalculator(TaxCalculator):
    def __init__(self, rate: Decimal) -> None:
        # TODO Day 1
        #   - Validate 0 <= rate <= 1.
        #   - Reject float.
        #   - Store on self.
        if isinstance(rate, float):
            raise TypeError("Rate must be a Decimal")
        if rate < Decimal("0") or rate > Decimal("1"):
            raise ValueError("Rate must be between 0 and 1")
        self.rate = rate

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        # TODO Day 1
        #   - vat = taxable * self.rate
        #   - Return TaxBreakdown with one component (f"VAT {percent}%", vat) and total = vat.
        #   - Tip: format the rate as a percentage cleanly.
        vat_amount = taxable * self.rate
        pct_display = self.rate * Decimal("100")
        label = f"VAT {pct_display:g}%"
        return TaxBreakdown(components=[(label, vat_amount)], total=vat_amount)
