# Mubashir Bashir 1-July-2025

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
        _("Payment Entry") + ":Link/Payment Entry:220",
        _("Supplier") + ":Link/Supplier:140",
        _("Payment Section") + ":Data:140",
        _("TaxPayer NTN") + ":Data:140",
        _("TaxPayer CNIC") + ":Data:140",
        _("TaxPayer Name") + ":Data:140",
        _("TaxPayer City") + ":Data:140",
        _("TaxPayer Address") + ":Data:140",
        _("TaxPayer Status") + ":Data:140",
        _("TaxPayer Business Name") + ":Data:140",
        _("Taxable Amount") + ":Data:140",
        _("Tax Amount") + ":Data:140",
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
            p.name, p.party, p.tax_withholding_category, s.tax_id, s.cnic, s.supplier_name, ad.city,
            s.supplier_primary_address, s.supplier_type, s.supplier_name, p.paid_amount, t.tax_amount
        FROM 
            `tabPayment Entry` as p
        LEFT JOIN `tabSupplier` as s ON p.party = s.name
        LEFT JOIN `tabAddress` as ad ON s.supplier_primary_address = ad.name
        LEFT JOIN `tabAdvance Taxes and Charges` as t ON t.parent = p.name AND t.account_head = 'Income Tax Account - AKFP'
        WHERE
            p.docstatus = 1  AND p.apply_tax_withholding_amount = 1 {0}
        ORDER BY 
            p.party
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result

# def get_query_result(filters):
#     conditions = get_conditions(filters)
#     result = frappe.db.sql(
#         """
#         SELECT 
# 			"Tax Category", "NTN", custom_cnic, employee_name, 'City', custom_employee_address, 'Individual', "Business Name", gross_pay, current_month_income_tax
#         FROM 
#             `tabSalary Slip`
#         WHERE
#             docstatus = 1
#         {0}
#     """.format(
#             conditions if conditions else ""
#         ),
#         filters,
#         as_dict=0,
#     )
#     return result
