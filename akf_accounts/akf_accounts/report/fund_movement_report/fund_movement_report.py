# Mubashir Bashir 17-03-2025

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
        _("Service Area") + ":Link/Service Area:140",
        _("Subservice Area") + ":Link/Subservice Area:140",
        _("Product") + ":Link/Product:140",
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
    year_start_date, year_end_date = fiscal_year_dates
    company = filters.get("company")
    cost_centers = filters.get("cost_center")
    service_area = filters.get("service_area")
    subservice_area = filters.get("subservice_area")
    product = filters.get("product")
    project = filters.get("project")
    
    balance_data = {}  

    # Dynamic WHERE clause for filters
    where_conditions = ["d.company = %(company)s", "d.posting_date BETWEEN %(start_date)s AND %(end_date)s"]
    query_params = {"company": company, "start_date": year_start_date, "end_date": year_end_date}

    if cost_centers:
        where_conditions.append("d.donation_cost_center IN %(cost_center)s")
        query_params["cost_center"] = tuple(cost_centers) if isinstance(cost_centers, list) else (cost_centers,)
    if service_area:
        where_conditions.append("pd.service_area = %(service_area)s")
        query_params["service_area"] = service_area
    if subservice_area:
        where_conditions.append("pd.subservice_area = %(subservice_area)s")
        query_params["subservice_area"] = subservice_area
    if product:
        where_conditions.append("pd.product = %(product)s")
        query_params["product"] = product
    if project:
        where_conditions.append("pd.project_id = %(project)s")
        query_params["project"] = project

    where_clause = " AND ".join(where_conditions)

    income_data = frappe.db.sql(
        f"""
        SELECT db.income_type, SUM(db.amount) AS amount, d.donation_cost_center, pd.service_area, pd.subservice_area, pd.product, pd.project_id
        FROM `tabDonation` AS d
        INNER JOIN `tabPayment Detail` AS pd ON pd.parent = d.name
        INNER JOIN `tabDeduction Breakeven` AS db ON db.parent = d.name AND db.random_id = pd.random_id
        WHERE {where_clause}
        GROUP BY db.income_type, d.donation_cost_center, pd.service_area, pd.subservice_area, pd.product, pd.project_id
        """,
        query_params,
        as_dict=True
    )

    for entry in income_data:
        key = (company, entry.get("donation_cost_center"), entry.get("service_area"), entry.get("subservice_area"), entry.get("product"), entry.get("project_id"))
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

    if cost_centers:
        gl_where_conditions.append("cost_center IN %(cost_center)s")
        gl_query_params["cost_center"] = tuple(cost_centers) if isinstance(cost_centers, list) else (cost_centers,)
    if service_area:
        gl_where_conditions.append("service_area = %(service_area)s")
        gl_query_params["service_area"] = service_area
    if subservice_area:
        gl_where_conditions.append("subservice_area = %(subservice_area)s")
        gl_query_params["subservice_area"] = subservice_area
    if product:
        gl_where_conditions.append("product = %(product)s")
        gl_query_params["product"] = product
    if project:
        gl_where_conditions.append("project = %(project)s")
        gl_query_params["project"] = project

    gl_where_clause = " AND ".join(gl_where_conditions)

    gl_entries = frappe.db.sql(
        f"""
        SELECT account, debit, credit, cost_center, service_area, subservice_area, product, project, posting_date, voucher_type, voucher_no
        FROM `tabGL Entry`
        WHERE {gl_where_clause}
        AND project != ''
        GROUP BY cost_center, service_area, subservice_area, product, project
        """,
        gl_query_params,
        as_dict=True
    )

    accounts = {acc.name: acc.account_type for acc in frappe.get_all("Account", fields=["name", "account_type"])}

    for entry in gl_entries:
        key = (company, entry.get("cost_center"), entry.get("service_area"), entry.get("subservice_area"), entry.get("product"), entry.get("project"))
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
        if entry['posting_date'] < year_start_date:
            balance_data[key]['opening_balance'] += balance
        elif entry['posting_date'] <= year_end_date:
            balance_data[key]['closing_balance'] += balance
        
        if entry['posting_date'] >= year_start_date and entry['posting_date'] <= year_end_date:
            if entry['voucher_type'] == 'Payment Entry':
                balance_data[key]['payment_others'] += entry['debit']
            elif entry['voucher_type'] == 'Funds Transfer':
                funds_transfer = frappe.get_doc('Funds Transfer', entry['voucher_no'], ['transaction_type', 'from_cost_center', 'to_cost_center'])
                if funds_transfer.transaction_type == 'Inter Fund':
                    balance_data[key]['inter_fund_sent'] += entry['debit']
                    balance_data[key]['inter_fund_received'] += entry['credit']
                elif funds_transfer.transaction_type == 'Inter Branch' and funds_transfer.from_cost_center != 'Main - AKFP':
                    balance_data[key]['inter_branch_sent_exc_ho'] += entry['debit']
                elif funds_transfer.transaction_type == 'Inter Branch' and funds_transfer.to_cost_center != 'Main - AKFP':
                    balance_data[key]['inter_branch_received_exc_ho'] += entry['credit']
                elif funds_transfer.transaction_type == 'Inter Branch' and funds_transfer.from_cost_center == 'Main - AKFP':
                    balance_data[key]['inter_branch_sent_ho'] += entry['debit']
                elif funds_transfer.transaction_type == 'Inter Branch' and funds_transfer.to_cost_center == 'Main - AKFP':
                    balance_data[key]['inter_branch_received_ho'] += entry['credit']

        if accounts.get(entry['account']) == 'Receivable':
            if entry['posting_date'] < year_start_date:
                balance_data[key]['receivable_balance'] += balance
            elif entry['posting_date'] <= year_end_date:
                balance_data[key]['closing_receivable'] += balance


    # Converting dictionary data to report format
    report_data = [
        [
            company, cost_center, service_area, subservice_area, product, project,
            balances['opening_balance'], balances['receivable_balance'],
            balances['inter_fund_sent'], balances['inter_fund_received'],
            balances['inter_branch_sent_exc_ho'], balances['inter_branch_received_exc_ho'],
            balances['inter_branch_sent_ho'], balances['inter_branch_received_ho'],
            balances['payment_others'],
            balances['restricted_income'], balances['admin_income'],
            balances['endowment'], balances['fund_raising'],
            balances['closing_balance'], balances['closing_receivable']
        ]
        for (company, cost_center, service_area, subservice_area, product, project), balances in balance_data.items()
    ]

    return report_data


def get_fiscal_year_dates(filters):
    if not filters.get("fiscal_year"):
        return None
    fiscal_year = frappe.get_doc("Fiscal Year", filters.get("fiscal_year"))
    return fiscal_year.year_start_date, fiscal_year.year_end_date
