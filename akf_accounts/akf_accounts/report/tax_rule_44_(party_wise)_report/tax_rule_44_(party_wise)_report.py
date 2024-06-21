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
        _("NTN / CNIC") + ":Data:140",
        # _("GL") + ":Data:140",
        # _("Branch") + ":Data:140",
        # _("Tax Nature") + ":Data:140",
        # _("Voucher No") + ":Data:140",
        # _("Taxable Amount") + ":Data:140",
        # _("Deduction") + ":Data:140",
        # _("Deduction Date") + ":Date:140",
        # _("WH Tax Rate") + ":Data:140",
        # _("Section") + ":Data:140",
        # _("Cheque No") + ":Data:140",
        # _("Deposit") + ":Data:140",
        # _("Deposit Date") + ":Data:140",
        # _("CPAN") + ":Data:140",
        # _("Default Day(s)") + ":Data:140",
        # _("Bill") + ":Data:140",
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
