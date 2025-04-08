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
        _("Code") + ":Link/Donor:280",
        _("Donor Name") + ":Data:280",
        _("Account") + ":Data:280",
    ]
    return columns


def get_data(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
			name, donor_name, default_account            
        FROM 
            `tabDonor`
        WHERE
            status = 'Active'
        {0}
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("donor"):
        conditions += " AND name = %(donor)s"

    return conditions


