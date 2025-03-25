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
        _("Cost Center") + ":Data:140",
        _("Fund Class") + ":Link/Project:140",
        _("Voucher Type") + ":Data:140",
        _("Voucher No") + ":Data:140",
        _("Donor") + ":Link/Donor:140",
        _("Income") + ":Currency:140",
        _("Expense") + ":Currency:140",
        _("Difference") + ":Currency:140",
    ]

    return columns

def get_data(filters):
    result = get_query_result(filters)

    total_income = sum(row[5] for row in result)
    total_expense = sum(row[6] for row in result)
    total_difference = sum(row[7] for row in result)

    total_row = ("", "", "", "","Total:", total_income, total_expense, total_difference)
    result = list(result) + [total_row]

    return result

def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND company = %(company)s"
    if filters.get("branch"):
        conditions += " AND cost_center = %(branch)s"
    if filters.get("fund"):
        conditions += " AND project = %(fund)s"

    return conditions

def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
            cost_center, 
            project, 
            voucher_type, 
            voucher_no, 
            donor, 
            sum(credit), 
            sum(debit), 
            sum(credit-debit)
        FROM 
            `tabGL Entry`
        Where 
            is_cancelled=0
            AND ifnull(project, "") != ""
            AND account in (SELECT name FROM `tabAccount` WHERE root_type in ('Income', 'Expense'))
            {0}
        GROUP BY 
            cost_center, project, voucher_type, voucher_no
        ORDER BY
            cost_center,voucher_type
        """.format(
                conditions if conditions else ""
            ),
            filters,
            as_dict=0,
        )
    return result
