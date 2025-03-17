# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe import _

@frappe.whitelist(allow_guest=True)
def execute(filters=None):
    columns = get_columns()
    data = get_data(filters)
    return columns, data

def get_columns():
    return [
        _("Company") + ":Link/Company:140",
        _("Cost Center") + ":Link/Cost Center:140",
        _("Project") + ":Link/Project:140",
        _("Opening Balance") + ":Float:140",
        _("Opening Receivable") + ":Float:140",
        _("Inter-Fund Transfer From (Sent)") + ":Float:140",
        _("Inter-Fund Transfer To (Rec.)") + ":Float:140",
        _("Inter-Branch Transfer From(Exc. HO)") + ":Data:140",
        _("Inter-Branch Transfer To(Exc. HO)") + ":Data:140",
        _("Inter-Branch Transfer From(HO)") + ":Data:140",
        _("Inter-Branch Transfer To(HO)") + ":Data:140",
        _("Payment(Others)") + ":Data:140",
        _("Restricted Income") + ":Float:140",
        _("Admin Income") + ":Float:140",
        _("Endowment") + ":Float:140",
        _("Fund Raising") + ":Float:140",
        _("Closing Balance") + ":Float:140",
        _("Closing Receivable") + ":Float:140",
    ]

def get_data(filters):
    fiscal_year_dates = get_fiscal_year_dates(filters)
    
    if not fiscal_year_dates:
        frappe.throw(_("Fiscal Year is required"))

    year_start_date, year_end_date = fiscal_year_dates
    company = filters.get("company")
    cost_center = filters.get("cost_center")
    project = filters.get("project")
    
    balance_data = {}  # Dictionary to store aggregated data


    # Dynamic WHERE clause for filters
    where_conditions = ["d.company = %(company)s", "d.posting_date BETWEEN %(start_date)s AND %(end_date)s"]
    query_params = {"company": company, "start_date": year_start_date, "end_date": year_end_date}

    if cost_center:
        where_conditions.append("d.donation_cost_center = %(cost_center)s")
        query_params["cost_center"] = cost_center
    if project:
        where_conditions.append("pd.project_id = %(project)s")
        query_params["project"] = project

    where_clause = " AND ".join(where_conditions)

    income_data = frappe.db.sql(
        f"""
        SELECT db.income_type, SUM(db.amount) AS amount, d.donation_cost_center, pd.project_id
        FROM `tabDonation` AS d
        INNER JOIN `tabPayment Detail` AS pd ON pd.parent = d.name
        INNER JOIN `tabDeduction Breakeven` AS db ON db.parent = d.name AND db.random_id = pd.random_id
        WHERE {where_clause}
        GROUP BY db.income_type, d.donation_cost_center, pd.project_id
        """,
        query_params,
        as_dict=True
    )

    for entry in income_data:
        key = (company, entry.get("donation_cost_center"), entry.get("project_id"))
        balance_data.setdefault(key, {
            'opening_balance': 0, 'receivable_balance': 0,
            'closing_balance': 0, 'closing_receivable': 0,
            'inter_fund_sent': 0, 'inter_fund_received': 0,
            'inter_branch_sent_exc_ho': 0, 'inter_branch_received_exc_ho': 0,
            'inter_branch_sent_ho': 0, 'inter_branch_received_ho': 0,
            'payment_others': 0,
            'restricted_income': 0, 'admin_income': 0,
            'endowment': 0, 'fund_raising': 0
        })
        balance_data[key][entry["income_type"].lower().replace(" ", "_")] = entry["amount"]

    # Dynamic WHERE clause for gl_entries query
    gl_where_conditions = ["company = %(company)s", "docstatus = 1", "posting_date <= %(end_date)s"]
    gl_query_params = {"company": company, "end_date": year_end_date}

    if cost_center:
        gl_where_conditions.append("cost_center = %(cost_center)s")
        gl_query_params["cost_center"] = cost_center
    if project:
        gl_where_conditions.append("project = %(project)s")
        gl_query_params["project"] = project

    gl_where_clause = " AND ".join(gl_where_conditions)

    gl_entries = frappe.db.sql(
        f"""
        SELECT account, debit, credit, cost_center, project, posting_date
        FROM `tabGL Entry`
        WHERE {gl_where_clause}
        AND project != ''
        """,
        gl_query_params,
        as_dict=True
    )

    accounts = {acc.name: acc.account_type for acc in frappe.get_all("Account", fields=["name", "account_type"])}

    for entry in gl_entries:
        key = (company, entry.get("cost_center"), entry.get("project"))
        balance_data.setdefault(key, {
            'opening_balance': 0, 'receivable_balance': 0,
            'closing_balance': 0, 'closing_receivable': 0,
            'inter_fund_sent': 0, 'inter_fund_received': 0,
            'inter_branch_sent_exc_ho': 0, 'inter_branch_received_exc_ho': 0,
            'inter_branch_sent_ho': 0, 'inter_branch_received_ho': 0,
            'payment_others': 0,
            'restricted_income': 0, 'admin_income': 0,
            'endowment': 0, 'fund_raising': 0
        })

        balance = entry['credit'] - entry['debit']
        if entry['posting_date'] <= year_start_date:
            balance_data[key]['opening_balance'] += balance
        else:
            balance_data[key]['closing_balance'] += balance

        if accounts.get(entry['account']) == 'Receivable':
            if entry['posting_date'] <= year_start_date:
                balance_data[key]['receivable_balance'] += balance
            else:
                balance_data[key]['closing_receivable'] += balance


    # Converting dictionary data to report format
    report_data = [
        [
            company, cost_center, project,
            balances['opening_balance'], balances['receivable_balance'],
            balances['inter_fund_sent'], balances['inter_fund_received'],
            balances['inter_branch_sent_exc_ho'], balances['inter_branch_received_exc_ho'],
            balances['inter_branch_sent_ho'], balances['inter_branch_received_ho'],
            balances['payment_others'],
            balances['restricted_income'], balances['admin_income'],
            balances['endowment'], balances['fund_raising'],
            balances['closing_balance'], balances['closing_receivable']
        ]
        for (company, cost_center, project), balances in balance_data.items()
    ]

    return report_data


def get_fiscal_year_dates(filters):
    if not filters.get("fiscal_year"):
        return None
    fiscal_year = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    return fiscal_year.year_start_date, fiscal_year.year_end_date



# def get_data(filters):
#     fiscal_year_dates = get_fiscal_year_dates(filters)
    
#     if not fiscal_year_dates:
#         frappe.throw(_("Fiscal Year is required"))

#     year_start_date, year_end_date = fiscal_year_dates
#     company = filters.get("company")
    
#     balance_data = {}  # Dictionary to store aggregated data


#     income_data = frappe.db.sql(
#         """
#         SELECT db.income_type, sum(db.amount) as amount, d.donation_cost_center, pd.project_id
#         FROM `tabDonation` as d
#         INNER JOIN `tabPayment Detail` as pd ON pd.parent = d.name
#         INNER JOIN `tabDeduction Breakeven` as db ON db.parent = d.name AND db.random_id = pd.random_id
#         WHERE d.company = %(company)s
#         AND d.posting_date BETWEEN %(start_date)s AND %(end_date)s
#         GROUP BY db.income_type, d.donation_cost_center, pd.project_id
#         """,
#         {
#             "company": company,
#             "start_date": year_start_date,
#             "end_date": year_end_date,
#         }, as_dict=True
#     )

#     for entry in income_data:
#         key = (company, entry.get("donation_cost_center"), entry.get("project_id"))
#         if key not in balance_data:
#             balance_data[key] = {
#                 'opening_balance': 0, 'receivable_balance': 0,
#                 'closing_balance': 0, 'closing_receivable': 0,
#                 'inter_fund_sent': 0, 'inter_fund_received': 0,
#                 'inter_branch_sent_exc_ho': 0, 'inter_branch_received_exc_ho': 0,
#                 'inter_branch_sent_ho': 0, 'inter_branch_received_ho': 0,
#                 'payment_others': 0,
#                 'restricted_income': 0, 'admin_income': 0,
#                 'endowment': 0, 'fund_raising': 0
#             }
#         balance_data[key][entry["income_type"].lower().replace(" ", "_")] = entry["amount"]

#     # Fetch GL entries for both opening and closing balances
#     gl_filters = {
#         'company': company,
#         'docstatus': 1,
#         'project': ['!=', '']  # Exclude empty project values
#     }
#     if filters.get("cost_center"):
#         gl_filters["cost_center"] = filters.get("cost_center")
#     if filters.get("project"):
#         gl_filters["project"] = filters.get("project")

#     opening_gl_entries = frappe.get_all(
#         'GL Entry',
#         filters={**gl_filters, 'posting_date': ['<=', year_start_date]},
#         fields=['account', 'debit', 'credit', 'cost_center', 'project']
#     )

#     closing_gl_entries = frappe.get_all(
#         'GL Entry',
#         filters={**gl_filters, 'posting_date': ['<=', year_end_date]},
#         fields=['account', 'debit', 'credit', 'cost_center', 'project']
#     )

#     def process_entries(entries, key_name, receivable_key_name):
#         for entry in entries:
#             key = (company, entry.get("cost_center"), entry.get("project"))
#             if key not in balance_data:
#                 balance_data[key] = {
#                     'opening_balance': 0, 'receivable_balance': 0,
#                     'closing_balance': 0, 'closing_receivable': 0,
#                     'inter_fund_sent': 0, 'inter_fund_received': 0,
#                     'inter_branch_sent_exc_ho': 0, 'inter_branch_received_exc_ho': 0,
#                     'inter_branch_sent_ho': 0, 'inter_branch_received_ho': 0,
#                     'payment_others': 0,
#                     'restricted_income': 0, 'admin_income': 0,
#                     'endowment': 0, 'fund_raising': 0
#                 }

#             balance = entry['credit'] - entry['debit']
#             balance_data[key][key_name] += balance

#             account_type = frappe.db.get_value('Account', entry['account'], 'account_type')
#             if account_type == 'Receivable':
#                 balance_data[key][receivable_key_name] += balance

#     process_entries(opening_gl_entries, 'opening_balance', 'receivable_balance')
#     process_entries(closing_gl_entries, 'closing_balance', 'closing_receivable')

#     # Convert aggregated data to list format for report
#     report_data = []
#     for (company, cost_center, project), balances in balance_data.items():
#         report_data.append([
#             company,
#             cost_center,
#             project,
#             balances['opening_balance'],
#             balances['receivable_balance'],
#             balances['inter_fund_sent'],
#             balances['inter_fund_received'],
#             balances['inter_branch_sent_exc_ho'],
#             balances['inter_branch_received_exc_ho'],
#             balances['inter_branch_sent_ho'],
#             balances['inter_branch_received_ho'],
#             balances['payment_others'],
#             balances['restricted_income'],
#             balances['admin_income'],
#             balances['endowment'],
#             balances['fund_raising'],
#             balances['closing_balance'],
#             balances['closing_receivable'],
#         ])

#     return report_data

