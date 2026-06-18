from datetime import date, datetime
from decimal import Decimal

from billing_engine.pdf import InvoiceRenderer
from billing_engine.models import (
    Invoice,
    InvoiceLineItem,
    Customer,
    InvoiceStatus,
    LineItemKind
)

from billing_engine.money import Money



customer = Customer(
    id=1,
    name="Pratyusha",
    email="test@gmail.com",
    country_code="IN",
    state_code="OD"
)

invoice = Invoice(

    id=1,

    subscription_id=101,

    period_start=date(2026,6,1),

    period_end=date(2026,6,30),

    subtotal=Money(Decimal("1000"),"INR"),

    discount_total=Money(Decimal("0"),"INR"),

    tax_total=Money(Decimal("180"),"INR"),

    total=Money(Decimal("1180"),"INR"),

    status=InvoiceStatus.ISSUED,

    issued_at=datetime.now()
)



items = [

    InvoiceLineItem(

        id=1,

        invoice_id=1,

        description="Premium Subscription",

        amount=Money(Decimal("1000"),"INR"),

        kind=LineItemKind.BASE
    )

]



renderer = InvoiceRenderer()


pdf_path = renderer.render(

    invoice,

    customer,

    items

)


print("PDF created:")
print(pdf_path)