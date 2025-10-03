import frappe, ast

from akf_accounts.utils.accounts_defaults import get_company_defaults
# from akf_projects.customizations.overrides.project.financial_stats import (
# 	get_donation, 
# 	get_funds_transfer, 
# 	get_purchasing
# )
""" 
Nabeel Saleem
Date: 17-02-2025
"""
# 
@frappe.whitelist()
def get_donor_balances(filters=None):
	if(type(filters) == str): filters = ast.literal_eval(filters)
	
	accounts = get_company_defaults(filters.get("company"))

	query = """ 
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
			and ifnull(project, "")=""
			{0}
		Group By
			cost_center, account, donor
		Having
			balance>0
		Order By
			balance desc
	""".format(get_conditions(filters, accounts))

	response = frappe.db.sql(query, filters, as_dict=1)
	
	amount = filters.get("amount")
	
	for row in response:
		row["encumbrance_project_account"] = accounts.encumbrance_project_account
		row["encumbrance_material_request_account"] = accounts.encumbrance_material_request_account
		row["encumbrance_purchase_order_account"] = accounts.encumbrance_purchase_order_account
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
	conditions += " and fund_class = %(fund_class)s " if(filters.get('fund_class')) else ""
	conditions += " and project = %(project)s " if(filters.get('project')) else ""
	conditions += " and donor = %(donor)s " if(filters.get('donor')) else ""
	conditions += " and donor_type = %(donor_type)s " if(filters.get('donor_type')) else ""
	conditions += " and donor_desk = %(donor_desk)s " if(filters.get('donor_desk')) else ""
	conditions += " and donation_type = %(intention)s " if(filters.get('intention')) else ""
	conditions += " and transaction_type = %(transaction_type)s " if(filters.get('transaction_type')) else ""

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

@frappe.whitelist()
def get_link_records(filters):
	from erpnext.accounts.utils import get_fiscal_year
	if(isinstance(filters, str)):
		filters = frappe.json.loads(filters)
		
	purchase_receipt = frappe.db.get_value("Purchase Invoice Item", {"parent": filters.get("name")}, "purchase_receipt")
	material_request = frappe.db.get_value("Purchase Receipt Item", {"parent": purchase_receipt}, "material_request")
	payment_entry = frappe.db.sql("""Select parent from `tabPayment Entry Reference` where docstatus=1 and reference_name=%(name)s """, filters, as_dict=1)
	payment_entry = [d.parent for d in payment_entry]
	args = {
			"docstatus": 1,
			"encumbrance": 1,
			"company": filters.get("company"),
			# "cost_center": filters.get("cost_center"),
			"project": filters.get("project"),
			"fiscal_year": get_fiscal_year(filters.get("posting_date"))[0]
		}
	# frappe.throw(frappe.as_json(args))
	budget = frappe.db.get_value("Budget", args, "name")

	return {
		"purchase_receipt": purchase_receipt,
		"material_request": material_request,
		"budget": budget,
		"payment_entry": payment_entry
	}
	