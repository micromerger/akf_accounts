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
        _("Date") + ":Date:140",
        _("Donor") + ":Link/Donor:140",
        _("Voucher No") + ":Data:140",
        _("Branch From") + ":Data:140",
        _("Branch To") + ":Data:140",
        _("Service Area From") + ":Data:140",
        _("Service Area To") + ":Data:140",
        _("Subservice Area From") + ":Data:140",
        _("Subservice Area To") + ":Data:140",
        _("Project From") + ":Data:140",
        _("Project To") + ":Data:140",
        _("Status") + ":Data:140",
        _("Amount") + ":Data:140",
    ]
    return columns


def get_data(filters):
    result = get_query_result(filters)
    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("voucher_no"):
        conditions += " AND ft.name = %(voucher_no)s"
    if filters.get("donor"):
        conditions += " AND ftf.ff_donor = %(donor)s"
    if filters.get("branch"):
        conditions += " AND ft.custom_from_cost_center = %(branch)s"
    if filters.get("project"):
        conditions += " AND ftf.ff_project = %(project)s"

    return conditions


def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
			ft.posting_date,ftf.ff_donor,ft.name,ft.custom_from_cost_center,ft.custom_to_cost_center,ftf.ff_service_area,ftt.ft_service_area,ftf.ff_subservice_area,ftt.ft_subservice_area,ftf.ff_project,ftt.ft_project,
            CASE
                WHEN ft.docstatus = 0 THEN 'Pending'
                WHEN ft.docstatus = 1 THEN 'Acknowledged'
            END
            ,ftt.ft_amount
        FROM 
            `tabFunds Transfer` ft
        LEFT JOIN `tabFunds Transfer From` ftf ON ft.name = ftf.parent
        LEFT JOIN `tabFunds Transfer To` ftt ON ft.name = ftt.parent
        WHERE
            ft.docstatus != 2
        {0}
    """.format(
            conditions if conditions else ""
        ),
        filters,
        as_dict=0,
    )
    return result
