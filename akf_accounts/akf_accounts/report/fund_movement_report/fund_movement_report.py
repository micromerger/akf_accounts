# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

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
        _("Project") + ":Data:140",
    #     _("Balance AS AT June 30,2022") + ":Date:140",
    #     _("Receivable AS AT July 01,2022") + ":Date:140",
    #     _("Fund Receipt") + ":Data:140",
    #     _("Inter-Fund Transfer From(Sent)") + ":Data:140",
    #     _("Inter-Fund Transfer To(Rec.)") + ":Data:140",
    #     _("Inter-Branch Transfer From(Exc. HO)") + ":Data:140",
    #     _("Inter-Branch Transfer To(Exc. HO)") + ":Data:140",
    #     _("Inter-Branch Transfer From(HO)") + ":Data:140",
    #     _("Inter-Branch Transfer To(HO)") + ":Data:140",
    #     _("Other Transfer Debit") + ":Data:140",
    #     _("Other Transfer Credit") + ":Data:140",
    #     _("Payment(Others)") + ":Data:140",
    #     _("Transferd to Designated Assets") + ":Data:140",
    #     _("Restricted Income") + ":Data:140",
    #     _("Admin Income") + ":Data:140",
    #     _("Endownment") + ":Data:140",
    #     _("Fund Raising") + ":Data:140",
    #     _("Receivable AS AT June 30,2023") + ":Date:140",
    #     _("Balance AS AT June 30,2023") + ":Date:140",        
    ]
    return columns


def get_data(filters):
    result = get_query_result(filters)
    return result


def get_conditions(filters):
    conditions = ""

    # if filters.get("company"):
    #     conditions += " AND company = %(company)s"
    # if filters.get("applicant"):
    #     conditions += " AND applicant = %(applicant)s"
    # if filters.get("branch"):
    #     conditions += " AND branch = %(branch)s"
    # if filters.get("loan_type"):
    #     conditions += " AND loan_type = %(loan_category)s"
    # if filters.get("repayment_start_date"):
    #     conditions += " AND repayment_start_date = %(repayment_start_date)s"

    return conditions


def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
			name
        FROM 
            `tabGL Entry`
        WHERE
            docstatus != 2
        {0}
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result
