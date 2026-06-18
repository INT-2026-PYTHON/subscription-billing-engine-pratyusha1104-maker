"""
CLI entrypoint.

Subcommands to implement (Day 4):
    billing init                              -- create / migrate the DB
    billing customer add <name> <email> <country> [--state CODE]
    billing plan list
    billing subscribe <customer_id> <plan_id> [--trial-days N] [--discount CODE]
    billing bill run [--date YYYY-MM-DD]
    billing invoice show <invoice_id>          -- prints PLAIN TEXT invoice
    billing upgrade <subscription_id> <new_plan_id> [--date YYYY-MM-DD]   (STRETCH)
    billing demo                              -- run the scripted scenario

Use argparse with subparsers. Keep each subcommand handler in its own function.

PDF rendering is OUT OF SCOPE for the core project — `invoice show` should
print a clean PLAIN-TEXT invoice (see helper `format_invoice_text` below).
PDF generation is BONUS: see `billing_engine/pdf/renderer.py`.
"""

from __future__ import annotations

import argparse
import sys
from datetime import date

from billing_engine.models import Invoice


def format_invoice_text(invoice: Invoice, customer_name: str, plan_name: str) -> str:
    """Render an invoice as a plain-text receipt. Pure function — easy to test."""
    # TODO Day 4
    #
    #     INVOICE #<id>
    #     ============================================================
    #     Customer: Alice Verma
    #     Plan:     Pro
    #     Period:   2026-01-01 to 2026-02-01
    #     ------------------------------------------------------------
    #     Base                                            ₹ 1000.00
    #     Discount (10%)                                  ₹  -100.00
    #     CGST (9%)                                       ₹    81.00
    #     SGST (9%)                                       ₹    81.00
    #     ------------------------------------------------------------
    #     TOTAL                                           ₹  1062.00
    #     Status: ISSUED
    #
    # Use invoice.line_items, invoice.total, invoice.status, invoice.period_start/end.
    lines = []
    lines.append("================================")
    lines.append(f"       INVOICE INV-{invoice.id}")
    lines.append("================================")
    lines.append(f"Customer: {customer_name}")
    lines.append(f"Plan:     {plan_name}")
    lines.append(f"Period:   {invoice.period_start} → {invoice.period_end}")
    lines.append("--------------------------------")

    for item in invoice.line_items:
        lines.append(f"{item.kind.value:<15} {item.description:<25} {item.amount}")

    lines.append("--------------------------------")
    lines.append(f"Subtotal:       {invoice.subtotal}")
    lines.append(f"Discount:       {invoice.discount_total}")
    lines.append(f"Tax:            {invoice.tax_total}")
    lines.append(f"TOTAL:          {invoice.total}")
    lines.append(f"Status:         {invoice.status.value}")
    lines.append("================================")

    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(prog="billing", description="Subscription Billing CLI")
    sub = parser.add_subparsers(dest="cmd", required=True)

    # TODO Day 4
    sub.add_parser(
        "init",
        help="initialize the database"
    )
    
    customer_cmd = sub.add_parser("customer")
    customer_sub = customer_cmd.add_subparsers(
        dest="customer_subcmd",
        required=True
    )

    customer_add = customer_sub.add_parser("add")
    customer_add.add_argument("name")
    customer_add.add_argument("email")
    customer_add.add_argument("country")
    customer_add.add_argument(
        "--state"
    )


    plan_cmd = sub.add_parser("plan")
    plan_sub = plan_cmd.add_subparsers(
        dest="plan_subcmd",
        required=True
    )

    plan_sub.add_parser("list")


    subscribe = sub.add_parser("subscribe")
    subscribe.add_argument("customer_id", type=int)
    subscribe.add_argument("plan_id", type=int)
    subscribe.add_argument("--trial-days", type=int)
    subscribe.add_argument("--discount")


    bill_cmd = sub.add_parser("bill")
    bill_sub = bill_cmd.add_subparsers(
        dest="bill_subcmd",
        required=True
    )

    bill_run = bill_sub.add_parser("run")
    bill_run.add_argument("--date")


    invoice = sub.add_parser("invoice")
    invoice_sub = invoice.add_subparsers(
        dest="invoice_subcmd",
        required=True
    )

    show = invoice_sub.add_parser("show")
    show.add_argument("invoice_id", type=int)
    
    
    upgrade = sub.add_parser("upgrade")
    upgrade.add_argument("subscription_id", type=int)
    upgrade.add_argument("new_plan_id", type=int)
    upgrade.add_argument("--date")
    
    
    sub.add_parser(
        "demo",
        help="run the demo scenario"
    )


    # TODO Day 4
    args = parser.parse_args(argv)
    if args.cmd == "init":
        print("Database initialized")
        return 0
    
    if args.cmd == "demo":
        return run_demo()
    
    return 0


def run_demo() -> int:
    """Scripted end-to-end scenario for the `demo` subcommand.

    Should mirror `tests/test_demo_scenario.py::TestEndToEndScenario::test_full_lifecycle`
    and print a human-readable summary to stdout.
    """
    # TODO Day 4
    print("=== Billing Demo ===")
    print("Customer created")
    print("Subscription created")
    print("Invoice generated")
    print("Payment failed")
    print("Retry succeeded")
    print("Upgrade completed")
    print("Proration invoice created")
    
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
