"""
BillingCycle — finds due subscriptions, generates invoices, posts ledger DEBITs,
advances the subscription period. Must be IDEMPOTENT (safe to run twice).
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date, datetime
import sqlite3
from typing import Callable, Optional

from billing_engine.db import (
    Database,
    CustomerRepository, PlanRepository, SubscriptionRepository,
    UsageRecordRepository, InvoiceRepository, InvoiceLineItemRepository,
    LedgerRepository,
)
from billing_engine.models import (Subscription,Invoice,InvoiceStatus,InvoiceLineItem,LineItemKind)
from billing_engine.billing.proration import compute_proration
from billing_engine.models.ledger import LedgerDirection, LedgerEntry
from billing_engine.money import Money
@dataclass
class BillingResult:
    invoices_created: int
    invoices_skipped_duplicate: int
    trials_activated: int


class BillingCycle:
    """Day-3 deliverable. Day-4 stretch: add `upgrade_subscription(...)`."""

    def __init__(
        self,
        db: Database,
        customer_repo: CustomerRepository,
        plan_repo: PlanRepository,
        subscription_repo: SubscriptionRepository,
        usage_repo: UsageRecordRepository,
        invoice_repo: InvoiceRepository,
        line_item_repo: InvoiceLineItemRepository,
        ledger_repo: LedgerRepository,
        strategy_factory: Callable,    # given a Plan, returns a PricingStrategy
        discount_factory: Callable,    # given a discount_id or None, returns a Discount or None
        tax_factory: Callable,         # given a Customer, returns (TaxCalculator, TaxContext)
    ) -> None:
        self.db = db
        self.customer_repo = customer_repo
        self.plan_repo = plan_repo
        self.subscription_repo = subscription_repo
        self.usage_repo = usage_repo
        self.invoice_repo = invoice_repo
        self.line_item_repo = line_item_repo
        self.ledger_repo = ledger_repo
        self.strategy_factory = strategy_factory
        self.discount_factory = discount_factory
        self.tax_factory = tax_factory

    # --------------------------------------------------------
    def run(self, as_of: date) -> BillingResult:
        """Bill all subscriptions whose current period ends on or before `as_of`."""
        # TODO Day 3
        invoices_created = 0
        invoices_skipped_duplicate = 0
        trials_activated = 0
        all_subscriptions = list(self.subscription_repo.list_all())
        for sub in all_subscriptions:
            if sub.status.value == "TRIAL" and sub.trial_end and sub.trial_end <= as_of:
                from billing_engine.models import SubscriptionStatus
                self.subscription_repo.update_status(sub.id, SubscriptionStatus.ACTIVE)
                trials_activated += 1
        due = list(self.subscription_repo.get_due_for_billing(as_of))
        
        for sub in due:
            plan = self.plan_repo.get(sub.plan_id)
            customer = self.customer_repo.get(sub.customer_id)
            strategy = self.strategy_factory(plan)
            discount = self.discount_factory(sub.discount_id) if sub.discount_id else None
            tax_calc, tax_context = self.tax_factory(customer)
            usage = self.usage_repo.sum_for_period(sub.id, "units", sub.current_period_start, sub.current_period_end)
            invoice_count = self.invoice_repo.count_for_subscription(sub.id)

            from billing_engine.billing.pipeline import build_invoice
            draft = build_invoice(
                subscription=sub,
                plan=plan,
                strategy=strategy,
                discount=discount,
                tax_calc=tax_calc,
                tax_context=tax_context,
                usage_quantity=usage,
                period_start=sub.current_period_start,
                period_end=sub.current_period_end,
                invoice_count_so_far=invoice_count,
            )
            from billing_engine.models import InvoiceStatus
            from datetime import UTC, datetime
            draft.status = InvoiceStatus.ISSUED
            draft.issued_at = datetime.now(UTC)

            try:
                saved_invoice = self.invoice_repo.add(draft)
                for line in draft.line_items:
                    line_with_true_id = line.__class__(
                        id=None,
                        invoice_id=saved_invoice.id,
                        description=line.description,
                        amount=line.amount,
                        kind=line.kind,
                    )
                    self.line_item_repo.add(line_with_true_id)

                ledger_debit = LedgerEntry(
                    id=None,
                    invoice_id=saved_invoice.id,
                    customer_id=sub.customer_id,
                    amount=Money(
                        str(saved_invoice.total.amount),
                        plan.currency,
                    ),
                    direction=LedgerDirection.DEBIT,
                    reason=f"Invoice #{saved_invoice.id}",
                    created_at=datetime.now(UTC),
                )
                self.ledger_repo.add(ledger_debit)
                from billing_engine.models.plan import BillingPeriod
                new_start = sub.current_period_end
                if plan.billing_period == BillingPeriod.MONTHLY:
                    year = new_start.year
                    month = new_start.month + 1
                    if month > 12:
                        month = 1
                        year += 1
                    new_end = date(year, month, new_start.day)
                elif plan.billing_period == BillingPeriod.YEARLY:
                    new_end = date(
                        new_start.year + 1,
                        new_start.month,
                        new_start.day,
                    )
                else:
                    raise ValueError(
                        f"Unsupported billing period: {plan.billing_period}"
                    )
                
                self.subscription_repo.update_period(
                    sub.id,
                    new_start,
                    new_end,
                )
                invoices_created += 1
            except sqlite3.IntegrityError:
                invoices_skipped_duplicate += 1

        return BillingResult(
            invoices_created=invoices_created, 
            invoices_skipped_duplicate=invoices_skipped_duplicate, 
            trials_activated=trials_activated
        )
    
    def upgrade_subscription(
            self,
            subscription_id: int,
            new_plan_id: int,
            switch_date: date,):
        with self.db.transaction() as conn:
            subscription = self.subscription_repo.get(subscription_id)
            
            old_plan = self.plan_repo.get(subscription.plan_id)
            new_plan = self.plan_repo.get(new_plan_id)
            customer = self.customer_repo.get(subscription.customer_id)
            
            old_price = Money(
                str(old_plan.price),
                old_plan.currency
            )
            
            new_price = Money(
                str(new_plan.price),
                new_plan.currency
            )
            
            tax_calc, tax_context = self.tax_factory(customer)
            pr = compute_proration(
                old_price,
                new_price,
                subscription.current_period_start,
                subscription.current_period_end,
                switch_date,
                tax_calc,
                tax_context,
            )
            
            
            invoice = self.invoice_repo.add(
                Invoice(
                    id=None,subscription_id=subscription_id,
                    period_start=subscription.current_period_start,
                    period_end=subscription.current_period_end,
                    subtotal=pr.charge_amount - pr.credit_amount,
                    discount_total=Money("0", old_plan.currency),
                    tax_total=pr.charge_tax - pr.credit_tax,
                    total=pr.charge_amount - pr.credit_amount,
                    status=InvoiceStatus.ISSUED,
                )
            )


            self.line_item_repo.add(
                InvoiceLineItem(
                    id=None,
                    invoice_id=invoice.id,
                    description="Proration credit",
                    amount=Money(
                        str(-pr.credit_amount.amount),
                        pr.credit_amount.currency
                    ),
                    kind=LineItemKind.PRORATION_CREDIT,
                )
            )


            self.line_item_repo.add(
                InvoiceLineItem(
                    id=None,
                    invoice_id=invoice.id,
                    description="Proration charge",
                    amount=pr.charge_amount,
                    kind=LineItemKind.PRORATION_CHARGE,
                )
            )
            
            
            self.ledger_repo.add(
                LedgerEntry(
                    id=None,
                    invoice_id=invoice.id,
                    customer_id=subscription.customer_id,
                    amount=invoice.total,
                    direction=LedgerDirection.DEBIT,
                    reason=f"Upgrade invoice #{invoice.id}",
                )
            )
            
            
            self.subscription_repo.update_plan(
                subscription_id,
                new_plan_id
            )
    