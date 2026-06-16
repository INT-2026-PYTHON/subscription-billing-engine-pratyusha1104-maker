"""
GSTCalculator — Indian Goods & Services Tax.

The rule:
    - If customer_state == seller_state (or seller_state is "")  =>  intra-state
        -> charge CGST + SGST (split equally, e.g. 9% + 9% = 18%)
    - Else  =>  inter-state
        -> charge IGST (e.g. 18%)

Customers without a state code default to IGST (safe choice).
"""

from decimal import Decimal

from billing_engine.money import Money
from billing_engine.taxes.base import TaxCalculator, TaxContext, TaxBreakdown


class GSTCalculator(TaxCalculator):
    def __init__(self, cgst: Decimal, sgst: Decimal, igst: Decimal) -> None:
        # TODO Day 1
        #   - Validate each rate is Decimal in [0, 1].
        #   - Validate cgst + sgst == igst (sanity check on Indian GST setup).
        #   - Store on self.
        for r in (cgst, sgst, igst):
            if isinstance(r, float):
                raise TypeError("Rates must be Decimal instances")
            if r < Decimal("0") or r > Decimal("1"):
                raise ValueError("Rates must fall within 0 and 1 inclusive")
                
        if (cgst + sgst) != igst:
            raise ValueError("cgst + sgst must perfectly match igst")
            
        self.cgst_rate = cgst
        self.sgst_rate = sgst
        self.igst_rate = igst

    def apply(self, taxable: Money, context: TaxContext) -> TaxBreakdown:
        # TODO Day 1
        #   - Decide intra vs inter-state from context.
        #     intra = bool(context.customer_state) and context.customer_state == context.seller_state
        #   - If intra: components = [("CGST X%", taxable*cgst), ("SGST Y%", taxable*sgst)], total = sum
        #   - Else:     components = [("IGST Z%", taxable*igst)],                            total = igst leg
        intra = bool(context.customer_state) and context.customer_state == context.seller_state
        
        if intra:
            cgst_amt = taxable * self.cgst_rate
            sgst_amt = taxable * self.sgst_rate
            
            c_lbl = f"CGST {self.cgst_rate * Decimal('100'):g}%"
            s_lbl = f"SGST {self.sgst_rate * Decimal('100'):g}%"
            
            return TaxBreakdown(
                components={c_lbl: cgst_amt, s_lbl: sgst_amt},
                total=cgst_amt + sgst_amt
            )
        else:  
            igst_amt = taxable * self.igst_rate
            i_lbl = f"IGST {self.igst_rate * Decimal('100'):g}%"
            
            return TaxBreakdown(
                components={i_lbl: igst_amt},
                total=igst_amt
            )
        