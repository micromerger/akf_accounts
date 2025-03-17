import frappe, ast

from akf_accounts.utils.accounts_defaults import get_company_defaults
from akf_projects.customizations.overrides.project.financial_stats import (
	get_donation, 
	get_funds_transfer, 
	get_purchasing
)
""" 
Nabeel Saleem
Date: 17-02-2025
"""
# 
@frappe.whitelist()
def get_donor_balance(filters=None):
	if(type(filters) == str): filters = ast.literal_eval(filters)
	
	accounts = get_company_defaults(filters.get("company"))
	
	response = frappe.db.sql(""" 
 		Select 
   			cost_center, account, donor, 
			(select donor_name from `tabDonor` where name=gl.donor limit 1) as donor_name,
			sum(credit-debit) as balance

		From 
  			`tabGL Entry` gl
		Where 
  			docstatus=1
			and is_cancelled=0
			and account in (select name from tabAccount where account_type="Equity")
			{0}
		Group By
			cost_center, account, donor
		Having
			balance>0
		Order By
			balance desc
	""".format(get_conditions(filters, accounts)), filters, as_dict=1)
	
	amount = filters.get("amount")
	
	for row in response:
		row["encumbrance_project_account"] = accounts.encumbrance_project_account
		row["encumbrance_material_request_account"] = accounts.encumbrance_material_request_account
		row["amortise_designated_asset_fund_account"] = accounts.default_designated_asset_fund_account
		row["amortise_inventory_fund_account"] = accounts.default_inventory_fund_account
		if(row.balance<=amount):
			amount -= row.balance
			row["__checked"] = 1
		elif(amount>0 and row.balance>=amount):
			amount -= amount
			row["__checked"] = 1
		
	return response

def get_conditions(filters, accounts):
	conditions = " and company = %(company)s " if(filters.get('company')) else ""
	conditions += " and cost_center = %(cost_center)s " if(filters.get('cost_center')) else ""
	conditions += " and service_area = %(service_area)s " if(filters.get('service_area')) else ""
	conditions += " and subservice_area = %(subservice_area)s " if(filters.get('subservice_area')) else ""
	conditions += " and product = %(product)s " if(filters.get('product')) else ""
	conditions += " and project = %(project)s " if(filters.get('project')) else ""
	
	doctype = filters.get('doctype')
	
	if(doctype == "Material Request"):
		conditions += " and account = %(account)s "	
		filters.update({'account': accounts.encumbrance_project_account})
	elif(doctype == "Payment Entry"):
		conditions += " and account = %(account)s "	
		filters.update({'account': accounts.encumbrance_material_request_account})
	elif(doctype == "Budget"):
		conditions += " and account not like '%%encumbrance%%' "

	return conditions

