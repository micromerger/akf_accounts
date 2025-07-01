# Developer Mubashir Bashir, 1-July-2025

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
        _("Payment Entry") + ":Link/Payment Entry",
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
    result = get_query_result(filters)
    return result

def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND p.company = %(company)s"
    if filters.get("party"):
        conditions += " AND p.party = %(party)s"
    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND p.posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("payment_entry"):
        entries = filters.get("payment_entry")
        conditions += " AND p.name IN %(payment_entry)s"
        filters["payment_entry"] = tuple(entries)

    return conditions

def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
            p.name, p.party, s.tax_id, s.supplier_name, p.custom_tax_type_id_st,
            (SELECT COUNT(*) FROM `tabPayment Entry Reference` as per where per.parent = p.name) + 1 as invoice_count, 
            t.custom_tax_applicable_amount, t.tax_amount
        FROM 
            `tabPayment Entry` as p
        LEFT JOIN `tabSupplier` as s ON p.party = s.name
        LEFT JOIN `tabAdvance Taxes and Charges` as t ON t.parent = p.name AND t.account_head = 'Sales Tax and Province Account - AKFP'
        WHERE
            p.docstatus = 1 AND p.custom_sales_tax_and_province = 1 AND p.custom_authority = 'FBR' {0}
        ORDER BY 
            p.party
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result