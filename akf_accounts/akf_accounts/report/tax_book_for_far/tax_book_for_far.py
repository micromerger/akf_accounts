#March 26, 2025

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
        _("Asset Category") + ":Data:140",
        _("Asset ID") + ":Data:140",
        _("Item Code") + ":Data:140",
        _("Description") + ":Data:140",
        _("Location") + ":Data:140",
        _("Department / Program") + ":Data:140",
        _("Person/Dept. In Custody") + ":Data:140",
        _("Year") + ":Data:140",
        _("Date of Acqusition") + ":Data:140",
        _("Cost Qty") + ":Data:140",
        _("Cost Amount") + ":Data:140",
        _("Cost Adjustment/Transfer/Disposal") + ":Data:140",
        _("Closing Balance") + ":Data:140",
        _("Rate%") + ":Data:140",
        _("AD Opening Balance") + ":Data:140",
        _("AD Days") + ":Data:140",
        _("AD For the year") + ":Data:140",
        _("AD Disposal / Transfer") + ":Data:140",
        _("AD Closing Balance") + ":Data:140",
        _("NBV Qty") + ":Data:140",
        _("NBV Amount") + ":Data:140"
    ]
    return columns


def get_data(filters):
    result = get_query_result(filters)
    return result


def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND company = %(company)s"

    return conditions


def get_query_result(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
        SELECT 
            asset_category,
            name,
			item_code,
            asset_name,
            location,
            department,
            custom_issued_to,
            YEAR(available_for_use_date),
            available_for_use_date,
            asset_quantity,
            gross_purchase_amount,
            "Cost Adjustment Transfer Disposal",
            "Closing Balance", 
            "Rate", 
            "AD Opening Balance",
            "AD Days",
            "AD For the Year",
            "AD Disposal Transfer",
            "Closing Balance","NBV Qty",
            "NBV Amount"
        FROM 
            `tabAsset`
        WHERE
            docstatus = 1
            {0}
        ORDER BY
            asset_category
        """.format(
                conditions if conditions else ""
            ),
            filters,
            as_dict=0,
        )
    return result
