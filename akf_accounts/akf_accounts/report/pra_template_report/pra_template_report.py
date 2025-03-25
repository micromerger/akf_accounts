# Developer Mubashir Bashir, 24-03-2025

import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def execute(filters=None):
    columns, data = [], []
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    columns = [
        _("Supplier") + ":Link/Supplier",
        _("TaxPayer NTN") + ":Data:140",
        _("TaxPayer Name") + ":Data:140",
        _("Type") + ":Data:140",
        _("No of Invoices") + ":Int:140",
        _("Sales Tax Charged") + ":Data:220",
        _("Sales Tax Deducted") + ":Data:220",
        
    ]
    return columns

def get_data(filters):
    payment_entry_conditions = get_payment_entry_conditions(filters)
    purchase_invoice_conditions = get_purchase_invoice_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
			s.name, s.tax_id, s.supplier_name, pe.payment_type,
            (
            SELECT COUNT(*) FROM `tabPurchase Invoice` as pi WHERE pi.docstatus = 1 and pi.supplier = s.name {1} 
            ) AS no_of_invoices,
            sum(pe.paid_amount), 
            sum(CASE WHEN atc.account_head = 'GST - AKFP' THEN atc.tax_amount ELSE 0 END) as gst_amount
        FROM 
            `tabSupplier` as s
        INNER JOIN `tabPayment Entry` as pe ON pe.party = s.name
        INNER JOIN `tabAdvance Taxes and Charges` as atc ON atc.parent = pe.name 
        WHERE
            pe.docstatus = 1 AND s.state = 'Punjab' {0}
        GROUP BY s.supplier_name
    """.format(
            payment_entry_conditions if payment_entry_conditions else "",
            purchase_invoice_conditions if purchase_invoice_conditions else "",
        ),
        filters,
        as_dict=0,
    )
    return result

def get_payment_entry_conditions(filters):
    conditions = ""

    if filters.get("from_date") and filters.get("to_date"):
        conditions += "AND pe.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    elif filters.get("from_date"):
        conditions += "AND pe.posting_date >= %(from_date)s"
    elif filters.get("to_date"):
        conditions += "AND pe.posting_date <= %(to_date)s"
    if filters.get("supplier"):
        conditions += "AND s.name = %(supplier)s"

    return conditions

def get_purchase_invoice_conditions(filters):
    conditions = ""

    if filters.get("from_date") and filters.get("to_date"):
        conditions += "AND pi.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    elif filters.get("from_date"):
        conditions += "AND pi.posting_date >= %(from_date)s"
    elif filters.get("to_date"):
        conditions += "AND pi.posting_date <= %(to_date)s"

    return conditions