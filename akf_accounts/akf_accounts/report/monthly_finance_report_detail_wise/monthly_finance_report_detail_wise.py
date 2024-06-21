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
        _("FP Code") + ":Data:140",
        # _("New Code") + ":Data:140",
        # _("Ref-A") + ":Data:140",
        # _("Area") + ":Data:140",
        # _("Org Class") + ":Data:140",
        # _("Sub-Area") + ":Data:140",
        # _("PT") + ":Data:140",
        # _("7-Service Areas") + ":Data:140",
        # _("Donor") + ":Data:140",
        # _("Donor Type") + ":Data:140",
        # _("Opening Balance") + ":Data:140",
        # _("Receipts") + ":Data:140",
        # _("Expenditure") + ":Data:140",
        # _("Inter Fund Transfer") + ":Data:140",
        # _("Closing Balance") + ":Data:140",
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
