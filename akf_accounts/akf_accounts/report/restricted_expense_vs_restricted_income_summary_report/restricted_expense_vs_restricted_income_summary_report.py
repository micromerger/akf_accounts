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
        _("Branch") + ":Data:140",
        _("Fund Class") + ":Link/Project:140",
        _("Income") + ":Currency:140",
        _("Expense") + ":Currency:140",
        _("Difference") + ":Currency:140",
    ]
    return columns

def get_data(filters):
    result = get_query_result(filters)

    total_income = sum(row[2] for row in result)
    total_expense = sum(row[3] for row in result)
    total_difference = sum(row[4] for row in result)

    total_row = ("","Total:", total_income, total_expense, total_difference)
    result = list(result) + [total_row]

    return result

def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
    if filters.get("branch"):
        conditions += " AND gle.cost_center = %(branch)s"

    return conditions

def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
            SELECT
                gle.cost_center,
                gle.project,
                SUM(gle.credit),
                SUM(gle.debit),
                SUM(gle.credit - gle.debit)
            FROM 
                `tabGL Entry` gle
            LEFT JOIN
                `tabAccount` ac ON gle.account = ac.name
            WHERE
                is_cancelled = 0
                AND ac.root_type in ('Expense','Income')
                AND ifnull(gle.project,"") != ""
                {0}
            GROUP BY 
                gle.cost_center, gle.project
            ORDER BY 
                gle.cost_center, gle.project
        """.format(
                conditions if conditions else ""
            ), filters, as_dict=0 )
    
    return result
