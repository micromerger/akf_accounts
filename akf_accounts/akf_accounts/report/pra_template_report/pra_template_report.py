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
        # _("Payment Entry") + ":Link/Payment Entry",
        _("Supplier") + ":Link/Supplier",
        _("TaxPayer NTN") + ":Data:140",
        _("TaxPayer Name") + ":Data:140",
        _("Type") + ":Data:140",
        _("No of Invoices") + ":Int:140",
        _("Taxable Amount") + ":Currency:220",
        _("Sales Tax Charged") + ":Currency:220",
        _("Sales Tax Deducted") + ":Currency:220",        
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
                p.party as taxPayer,  
                (select tax_id from `tabSupplier` where name=p.party) as taxId,
                (select supplier_name from `tabSupplier` where name=p.party) as taxPayerName,
                (p.custom_tax_type_id_st) as tax_type_id, 
                count(p.name) as no_of_invoices,
                sum(p.paid_amount) as paid_amount,
                sum(t.custom_tax_applicable_amount) as tax_applicable_amount, 
                sum(t.tax_amount) as tax_amount
                
            FROM 
                `tabPayment Entry` as p
            inner JOIN `tabAdvance Taxes and Charges` as t ON t.parent = p.name

            WHERE
                p.docstatus < 2 AND p.custom_sales_tax_and_province = 1 AND p.custom_authority = 'PRA'
                {0}
            Group By 
                p.party, p.custom_supplier, p.custom_tax_type_id_st
            ORDER BY 
                p.party
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result