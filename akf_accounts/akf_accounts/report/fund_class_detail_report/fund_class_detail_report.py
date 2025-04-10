# Mubashir Bashir, 09-04-2025

import frappe
from frappe import _

@frappe.whitelist()
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)

    return columns, data

def get_columns():
    return [
        _("Company") + ":Link/Company:140",
        _("Cost Center") + ":Link/Cost Center:140",
        _("Service Area") + ":Link/Service Area:180",
        _("Subservice Area") + ":Link/Subservice Area:180",
        _("Project") + ":Link/Project:180",
        _("Project Name") + ":Data:180",
        _("Project Type") + ":Data:180",
        # _("Inter-Fund Transfer Account") + ":Data:140",
        _("Amortization Account") + ":Data:140",
        _("Admin Income Account") + ":Data:140",
        _("Fund Equity Account") + ":Link/Account:140",
        _("Account") + ":Link/Account:140",
        _("Status") + ":Data:140",
    ]

def get_data(filters):
    result = frappe.db.sql("""
    SELECT gle.company, gle.cost_center, gle.service_area, gle.subservice_area, gle.project,
           p.project_name, p.project_type,
           CASE WHEN acc.root_type = 'Equity' THEN gle.account ELSE '' END AS amortization_account,
           CASE WHEN acc.root_type = 'Income' THEN gle.account ELSE '' END AS adming_income_account,
           CASE WHEN acc.root_type = 'Equity' THEN gle.account ELSE '' END AS fund_equity_account, 
           p.status
    FROM `tabGL Entry` as gle
    LEFT JOIN `tabProject` as p ON p.name = gle.project
    LEFT JOIN `tabAccount` as acc ON acc.name = gle.account
    WHERE gle.docstatus = 1 AND gle.project IS NOT NULL AND gle.account IS NOT NULL {conditions}
    GROUP BY gle.company, gle.cost_center, gle.service_area, gle.subservice_area, gle.project, gle.account
    """.format(conditions = get_conditions(filters)), filters, as_dict=True)

    return result

def get_conditions(filters):
    conditions = ''

    if filters.get('company'): conditions += " AND gle.company = %(company)s"
    if filters.get('cost_center'): conditions += " AND gle.cost_center = %(cost_center)s"
    if filters.get('service_area'): conditions += " AND gle.service_area = %(service_area)s"
    if filters.get('subservice_area'): conditions += " AND gle.subservice_area = %(subservice_area)s"
    if filters.get('project'): conditions += " AND gle.project = %(project)s"
    if filters.get('account'): conditions += " AND gle.account = %(account)s"
    if filters.get('from_date') and filters.get('to_date'):
        conditions += " AND gle.posting_date >= %(from_date)s AND gle.posting_date <= %(to_date)s"

    return conditions
