from frappe import _
import frappe
from frappe.utils import fmt_money

def get_data():
    return {
        "fieldname": "fund_class",
        "transactions": [
            {
                "label": _("Budget Info"),
                "items": ["Budget"]
            },
            {
                "label": _("Donation Info"),
                "items": ["Donation"]
            },
            {
                "label": _("Project Info"),
                "items": ["Project"]
            }
        ],
    }

@frappe.whitelist()
def get_fund_class_stats(fund_class):
    try:
        # Calculate remaining budget
        transfer_budget = 0.0
        remaining_budget = 0.0
        return {
            "total_budget": fmt_money(get_total_defined_budget(fund_class), currency="PKR"),
            "funds_received": fmt_money(get_funds(fund_class), currency="PKR"),
            "transfer_budget": fmt_money(transfer_budget, currency="PKR"),
            "remaining_budget": fmt_money(remaining_budget, currency="PKR")
        }
    except Exception as e:
        frappe.log_error(f"Error in get_fund_class_stats: {str(e)}", "Fund Class Dashboard Error")
        return {
            "total_budget": fmt_money(0, currency="PKR"),
            "funds_received": fmt_money(0, currency="PKR"),
            "transfer_budget": fmt_money(0, currency="PKR"),
            "remaining_budget": fmt_money(0, currency="PKR")
        } 

def get_total_defined_budget(fund_class):
     # Get total budget amount from Budget Account table
    return frappe.db.sql(f"""
            SELECT 
                COALESCE(SUM(ba.budget_amount), 0)
            FROM 
                `tabBudget` b JOIN `tabBudget Account` ba ON ba.parent = b.name
            WHERE 
                b.fund_class = "{fund_class}" 
                AND b.docstatus < 2
        """)[0][0] or 0.0
        
 
def get_funds(fund_class):
    return frappe.db.sql(f"""
                  Select 
                    sum(credit-debit) as balance
                    From 
                        `tabGL Entry` gl
                    Where 
                        docstatus=1
                        and is_cancelled=0
                        and ifnull(fund_class, "")!=""
                        and fund_class="{fund_class}"
                        and account in (select name from tabAccount where account_type="Equity")
                  """)[0][0] or 0.0

