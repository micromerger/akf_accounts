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
        _("Service Area") + ":Link/Program:140",
        _("Subservice Area") + ":Link/Subservice Area:140",
        _("Product") + ":Link/Product:140",
        _("Fund/Class") + ":Link/Project:140",
        _("Voucher No") + ":Link/Donation:140",
        _("Manual No") + ":Data:140",
        _("Amount") + ":Currency:140",
        _("Admin Income") + ":Currency:140",
        _("Fund Raising Income") + ":Currency:140",
        _("Endowment Income") + ":Currency:140",
        _("Admin Budget Fund") + ":Currency:140",
        _("Operation Budget Fund") + ":Currency:140",
        _("CMCDB Fund") + ":Currency:140",
        _("Net Amount") + ":Currency:140",
    ]
    return columns


def get_data(filters):
    result = get_query_result(filters)
    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("from_date") and filters.get("to_date"):
        conditions += " AND posting_date BETWEEN %(from_date)s AND %(to_date)s"
    if filters.get("donor"):
        conditions += " AND pd.donor_id = %(donor)s"
    if filters.get("program"):
        conditions += " AND pd.program = %(program)s"
    if filters.get("subservice_area"):
        conditions += " AND pd.subservice_area = %(subservice_area)s"
    if filters.get("product"):
        conditions += " AND pd.product = %(product)s"
    if filters.get("project"):
        conditions += " AND pd.project_id = %(project)s"

    return conditions


def get_query_result(filters):
    conditions = get_conditions(filters)
    order_by_branches = ""
    group_by_branches = ""
    if filters.get("group_by_branches"):
        order_by_branches = "ORDER BY pd.cost_center, pd.program"
        # group_by_branches = "GROUP BY pd.cost_center,pd.program"

    result = frappe.db.sql(
        """
        SELECT posting_date,pd.donor_id,pd.program,pd.subservice_area, pd.product, pd.project_id,d.name,pd.receipt_number,db.donation_amount,
        CASE 
            WHEN db.income_type = 'Admin Income' THEN db.amount
            ELSE 0
        END,
        CASE 
            WHEN db.income_type = 'Fund raising' THEN db.amount
            ELSE 0
        END,
        CASE 
            WHEN db.income_type = 'Endowment' THEN db.amount
            ELSE 0
        END,
        CASE 
            WHEN db.income_type = 'OFSP Admin budget' THEN db.amount
            ELSE 0
        END,
        CASE 
            WHEN db.income_type = 'OFSP Operational budget' THEN db.amount
            ELSE 0
        END,
        CASE 
            WHEN db.income_type = 'OFSP CMCDP budget' THEN db.amount
            ELSE 0
        END,
        pd.net_amount

        FROM `tabDonation` d
        LEFT JOIN `tabPayment Detail` pd ON d.name = pd.parent
        LEFT JOIN `tabDeduction Breakeven` db ON d.name = db.parent
        WHERE d.docstatus != 2 {0}
        {1}""".format(conditions if conditions else "",order_by_branches),
        filters,
        as_dict=0,
    )
    return result