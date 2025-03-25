# Developer Mubashir Bashir, 25-03-2025

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
        _("Company") + ":Link/Company:140",
        _("Branch") + ":Link/Cost Center:140",
        _("Code") + ":Data:140",
        _("Date") + ":Date:140",
        _("Payment Type") + ":Date:140",
        _("Status") + ":Data:140",
        _("Status Date") + ":Date:140",
        _("Prepared By") + ":Data:140",
        _("Approved By") + ":Data:140",
        _("Amount") + ":Currency:140",
    ]
    return columns


def get_data(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
            company, cost_center, name, posting_date, payment_type, status, modified, owner, modified_by, paid_amount            
        FROM 
            `tabPayment Entry`
        WHERE
            docstatus != 2
        {0}
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_list=True, 
    )

    total_amount = sum(row[-1] for row in result) if result else 0

    num_columns = len(result[0]) if result else 10
    total_row = ["" for _ in range(num_columns)]
    
    total_row[-2] = "<b>Total</b>"
    total_row[-1] = total_amount

    result.append(total_row)

    return result

def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND company = %(company)s"
    if filters.get("cost_center"):
        conditions += " AND cost_center = %(cost_center)s"
    if filters.get("status"):
        conditions += " AND status = %(status)s"

    return conditions
