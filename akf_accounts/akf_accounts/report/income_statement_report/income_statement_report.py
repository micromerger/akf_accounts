# Mubashir Bashir, 09-04-2025

import frappe
from frappe import _

@frappe.whitelist()
def execute(filters=None):
    columns = get_columns()
    data = []

    data.append({
        "description": "<b>INCOME ACCOUNT BALANCE</b>"
    })
    income_data = get_income_data(filters)
    data.extend(income_data["rows"])
    data.append(make_total_row(income_data["totals"], "Total Income"))
    data.append({})

    data.append({
        "description": "<b>EXPENSE ACCOUNT BALANCE</b>"
    })
    expense_data = get_expense_data(filters)
    data.extend(expense_data["rows"])
    data.append(make_total_row(expense_data["totals"], "Total Expense"))
    data.append({})

    net_income_total = {
        "balance_amount": income_data["totals"].get("balance_amount", 0) - expense_data["totals"].get("balance_amount", 0)
    }

    data.append(make_total_row(net_income_total, "NET INCOME"))
    data.append({})

    return columns, data

def get_columns():
    return [
        _("Company") + ":Link/Company:140",
        _("Cost Center") + ":Link/Cost Center:140",
        _("Service Area") + ":Link/Service Area:180",
        _("Project") + ":Link/Project:180",
        _("Account") + ":Link/Account:140",
        _("Description") + ":Data:220",
        _("Income and Expenditure Statement") + ":Data:220",
    ]


def get_income_data(filters):
    filters = frappe._dict(filters)
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    conditions = "gle.docstatus = 1 AND acc.root_type = 'Income'"

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
        params["company"] = filters.company
    if filters.get("cost_center"):
        conditions += " AND gle.cost_center IN %(cost_center)s"
        params["cost_center"] = tuple(filters.cost_center)
    if filters.get("account"):
        conditions += " AND gle.account IN %(account)s"
        params["account"] = tuple(filters.account)
    if filters.get("service_area"):
        conditions += " AND gle.service_area IN %(service_area)s"
        params["service_area"] = tuple(filters.service_area)
    if filters.get("project"):
        conditions += " AND gle.project IN %(project)s"
        params["project"] = tuple(filters.project)

    income_entries = frappe.db.sql("""
        SELECT
            gle.company, gle.cost_center, gle.service_area, gle.project, gle.account, sum(gle.credit - gle.debit) as balance_amount
        FROM `tabGL Entry` gle
        LEFT JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.posting_date >= %(from_date)s and gle.posting_date <= %(to_date)s and {conditions}
        GROUP BY gle.company, gle.cost_center, gle.service_area, gle.project, gle.account
    """.format(conditions=conditions), params, as_dict=True)

    totals = {
        "balance_amount": 0
    }

    rows = []
    for row in income_entries:
        totals["balance_amount"] += row.balance_amount or 0

        rows.append({
            "company": row.company,
            "cost_center": row.cost_center,
            "service_area": row.service_area,
            "project": row.project,
            "account": row.account,
            "description": "",
            "income_and_expenditure_statement": frappe.utils.fmt_money(row.balance_amount) or 0,
        })

    return {
        "rows": rows,
        "totals": totals
    }


def get_expense_data(filters):
    filters = frappe._dict(filters)
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    conditions = "gle.docstatus = 1 AND acc.root_type = 'Expense'"

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
        params["company"] = filters.company
    if filters.get("cost_center"):
        conditions += " AND gle.cost_center IN %(cost_center)s"
        params["cost_center"] = tuple(filters.cost_center)
    if filters.get("account"):
        conditions += " AND gle.account IN %(account)s"
        params["account"] = tuple(filters.account)
    if filters.get("service_area"):
        conditions += " AND gle.service_area IN %(service_area)s"
        params["service_area"] = tuple(filters.service_area)
    if filters.get("project"):
        conditions += " AND gle.project IN %(project)s"
        params["project"] = tuple(filters.project)

    expense_entries = frappe.db.sql("""
        SELECT
            gle.company, gle.cost_center, gle.service_area, gle.project, gle.account, sum(gle.debit - gle.credit) as balance_amount
        FROM `tabGL Entry` gle
        LEFT JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE gle.posting_date >= %(from_date)s and gle.posting_date <= %(to_date)s and {conditions}
        GROUP BY gle.company, gle.cost_center, gle.service_area, gle.project, gle.account
    """.format(conditions=conditions), params, as_dict=True)

    totals = {
        "balance_amount": 0
    }

    rows = []
    for row in expense_entries:
        totals["balance_amount"] += row.balance_amount or 0

        rows.append({
            "company": row.company,
            "cost_center": row.cost_center,
            "service_area": row.service_area,
            "project": row.project,
            "account": row.account,
            "description": "",
            "income_and_expenditure_statement": frappe.utils.fmt_money(row.balance_amount) or 0,
        })

    return {
        "rows": rows,
        "totals": totals
    }


def make_total_row(totals, label):
    return {
        "description": f"<b>{label}</b>",
        "income_and_expenditure_statement": frappe.utils.fmt_money(totals["balance_amount"])
    }
