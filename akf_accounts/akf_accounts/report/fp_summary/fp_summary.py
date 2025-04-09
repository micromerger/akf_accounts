# Mubashir Bashir, 27-03-2025

import frappe
from frappe import _

@frappe.whitelist()
def execute(filters=None):
    columns = get_columns()
    data = []

    data.append({
        "description": "<b><h4>FUNDS & LIABILITIES</h4></b>"
    })
    data.append({})

    data.append({
        "description": "<b>RESTRICTED FUNDS</b>"
    })
    restricted_data = get_fund_data(filters, "Restricted")
    data.extend(restricted_data["rows"])
    data.append(make_total_row(restricted_data["totals"], "Total Restricted"))
    data.append({})

    data.append({
        "description": "<b>UNRESTRICTED FUNDS</b>"
    })
    unrestricted_data = get_fund_data(filters, "Unrestricted")
    data.extend(unrestricted_data["rows"])
    data.append(make_total_row(unrestricted_data["totals"], "Total Unrestricted"))
    data.append({})

    grand_total = {
        key: (restricted_data["totals"].get(key, 0) or 0) + (unrestricted_data["totals"].get(key, 0) or 0)
        for key in [
            "opening_balance",
            "receipts",
            "expenditure",
            "funds_transfer_sent",
            "funds_transfer_receive",
            "closing_balance"
        ]
    }
    data.append(make_total_row(grand_total, "Total Funds"))
    data.append({})
    
    data.append({
		"description": "<b>LIABILITIES</b>"
	})    
    liabilities_data = get_liability_data(filters)
    data.extend(liabilities_data["rows"])
    data.append(make_total_row(liabilities_data["totals"], "Total Liabilities"))
    data.append({})

    total_funds_liabilities = {
        "opening_balance": (grand_total["opening_balance"] or 0) - (liabilities_data["totals"]["opening_balance"] or 0),
        "receipts": "",
        "expenditure": "",
        "funds_transfer_sent": "",
        "funds_transfer_receive": "",
        "closing_balance": (grand_total["closing_balance"] or 0) - (liabilities_data["totals"]["closing_balance"] or 0),
    }
    data.append({
        "description": "<b>Total Funds and Liabilities</b>",
        **total_funds_liabilities
    })
    data.append({})
    
    data.append({
		"description": "<b>AVAILABLE ASSETS AGAINST FUNDS</b>"
	})    
    asset_data = get_asset_data(filters)
    data.extend(asset_data["rows"])
    data.append(make_total_row(asset_data["totals"], "Total Assets"))

    return columns, data

def get_columns():
    return [
        _("Company") + ":Link/Company:140",
        _("Cost Center") + ":Link/Cost Center:140",
        _("Description") + ":Data:180",
        _("Opening Balance") + ":Data:140",
        _("Receipts") + ":Data:140",
        _("Expenditure") + ":Data:140",
        _("Funds Transfer Sent") + ":Data:180",
        _("Funds Transfer Receive") + ":Data:180",
        _("Closing Balance") + ":Data:140",
    ]

def get_fund_data(filters, fund_type):
    filters = frappe._dict(filters)
    conditions = "gle.docstatus = 1 AND sa.type = %(fund_type)s"
    params = {
        "company": filters.company,
        "from_date": filters.from_date,
        "to_date": filters.to_date,
        "fund_type": fund_type
    }

    if filters.get("cost_center"):
        conditions += " AND gle.cost_center IN %(cost_center)s"
        params["cost_center"] = tuple(filters.cost_center)
    if filters.get("service_area"):
        conditions += " AND gle.service_area = %(service_area)s"
        params["service_area"] = filters.service_area

    gle_entries = frappe.db.sql(f"""
        SELECT
            gle.company, gle.cost_center, sa.name AS service_area_name,
            SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.credit - gle.debit ELSE 0 END) AS opening_balance,
            SUM(CASE WHEN gle.voucher_type = 'Payment Entry' AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.credit - gle.debit ELSE 0 END) AS receipts,
            SUM(CASE WHEN acc.root_type = 'Expense' AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.debit - gle.credit ELSE 0 END) AS expenditure,
            SUM(CASE WHEN gle.voucher_type = 'Funds Transfer' AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.debit ELSE 0 END) AS funds_transfer_sent,
            SUM(CASE WHEN gle.voucher_type = 'Funds Transfer' AND gle.posting_date BETWEEN %(from_date)s AND %(to_date)s THEN gle.credit ELSE 0 END) AS funds_transfer_receive,
            SUM(CASE WHEN gle.posting_date <= %(to_date)s THEN gle.credit - gle.debit ELSE 0 END) AS closing_balance
        FROM `tabGL Entry` gle
        LEFT JOIN `tabAccount` acc ON gle.account = acc.name
        LEFT JOIN `tabService Area` sa ON gle.service_area = sa.name
        WHERE {conditions}
        GROUP BY gle.company, gle.cost_center, sa.name
    """, params, as_dict=True)

    total = {
        "opening_balance": 0,
        "receipts": 0,
        "expenditure": 0,
        "funds_transfer_sent": 0,
        "funds_transfer_receive": 0,
        "closing_balance": 0
    }

    result = []
    for row in gle_entries:
        total["opening_balance"] += row.opening_balance or 0
        total["receipts"] += row.receipts or 0
        total["expenditure"] += row.expenditure or 0
        total["funds_transfer_sent"] += row.funds_transfer_sent or 0
        total["funds_transfer_receive"] += row.funds_transfer_receive or 0
        total["closing_balance"] += row.closing_balance or 0

        result.append({
            "company": row.company,
            "cost_center": row.cost_center,
            "description": row.service_area_name,
            "opening_balance": row.opening_balance,
            "receipts": row.receipts,
            "expenditure": row.expenditure,
            "funds_transfer_sent": row.funds_transfer_sent,
            "funds_transfer_receive": row.funds_transfer_receive,
            "closing_balance": row.closing_balance,
        })

    return {
        "rows": result,
        "totals": total
    }

def get_liability_data(filters):
    filters = frappe._dict(filters)
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    conditions = "gle.docstatus = 1 AND acc.root_type = 'Liability'"

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
        params["company"] = filters.company
    if filters.get("cost_center"):
        conditions += " AND gle.cost_center IN %(cost_center)s"
        params["cost_center"] = tuple(filters.cost_center)

    liability_entries = frappe.db.sql("""
        SELECT
            gle.company,
            gle.cost_center,
            gle.account,
            SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.credit - gle.debit ELSE 0 END) AS opening_balance,
            SUM(CASE WHEN gle.posting_date <= %(to_date)s THEN gle.credit - gle.debit ELSE 0 END) AS closing_balance
        FROM `tabGL Entry` gle
        LEFT JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE {conditions}
        GROUP BY gle.company, gle.cost_center, gle.account
    """.format(conditions=conditions), params, as_dict=True)

    totals = {
        "opening_balance": 0,
        "receipts": "",
        "expenditure": "",
        "funds_transfer_sent": "",
        "funds_transfer_receive": "",
        "closing_balance": 0
    }

    rows = []
    for row in liability_entries:
        totals["opening_balance"] += row.opening_balance or 0
        totals["closing_balance"] += row.closing_balance or 0

        rows.append({
            "company": row.company,
            "cost_center": row.cost_center,
            "description": row.account,
            "opening_balance": row.opening_balance,
            "receipts": "",
            "expenditure": "",
            "funds_transfer_sent": "",
            "funds_transfer_receive": "",
            "closing_balance": row.closing_balance
        })

    return {
        "rows": rows,
        "totals": totals
    }

def get_asset_data(filters):
    filters = frappe._dict(filters)
    params = {
        "from_date": filters.from_date,
        "to_date": filters.to_date,
    }

    conditions = "gle.docstatus = 1 AND acc.root_type = 'Asset'"

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
        params["company"] = filters.company
    if filters.get("cost_center"):
        conditions += " AND gle.cost_center IN %(cost_center)s"
        params["cost_center"] = tuple(filters.cost_center)

    asset_entries = frappe.db.sql("""
        SELECT
            gle.company,
            gle.cost_center,
            gle.account,
            SUM(CASE WHEN gle.posting_date < %(from_date)s THEN gle.debit - gle.credit ELSE 0 END) AS opening_balance,
            SUM(CASE WHEN gle.posting_date <= %(to_date)s THEN gle.debit - gle.credit ELSE 0 END) AS closing_balance
        FROM `tabGL Entry` gle
        LEFT JOIN `tabAccount` acc ON gle.account = acc.name
        WHERE {conditions}
        GROUP BY gle.company, gle.cost_center, gle.account
    """.format(conditions=conditions), params, as_dict=True)

    totals = {
        "opening_balance": 0,
        "receipts": "",
        "expenditure": "",
        "funds_transfer_sent": "",
        "funds_transfer_receive": "",
        "closing_balance": 0
    }

    rows = []
    for row in asset_entries:
        totals["opening_balance"] += row.opening_balance or 0
        totals["closing_balance"] += row.closing_balance or 0

        rows.append({
            "company": row.company,
            "cost_center": row.cost_center,
            "description": row.account,
            "opening_balance": row.opening_balance,
            "receipts": "",
            "expenditure": "",
            "funds_transfer_sent": "",
            "funds_transfer_receive": "",
            "closing_balance": row.closing_balance
        })

    return {
        "rows": rows,
        "totals": totals
    }


def make_total_row(totals, label):
    return {
        "description": f"<b>{label}</b>",
        "opening_balance": totals["opening_balance"],
        "receipts": totals["receipts"],
        "expenditure": totals["expenditure"],
        "funds_transfer_sent": totals["funds_transfer_sent"],
        "funds_transfer_receive": totals["funds_transfer_receive"],
        "closing_balance": totals["closing_balance"]
    }
