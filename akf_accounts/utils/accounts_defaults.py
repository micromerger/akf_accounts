import frappe
from frappe.utils import get_link_to_form

def get_company_defaults(company):
	doc = frappe.get_doc("Company", company)  
	
	if (not doc.custom_default_fund):
		form_link = get_link_to_form("Company", company)
		frappe.throw(f"Please set account of {form_link}", title="Fund Account")
 	
	if (not doc.custom_default_designated_asset_fund_account):
		form_link = get_link_to_form("Company", company)
		frappe.throw(f"Please set account of {form_link}", title="Designated Asset Fund Account")

	if (not doc.custom_default_inventory_fund_account):
		form_link = get_link_to_form("Company", company)
		frappe.throw(f"Please set account of {form_link}", title="Designated Inventory Fund Account")

	if (not doc.custom_encumbrance_project_account):
		form_link = get_link_to_form("Company", company)
		frappe.throw(f"Please set account of {form_link}", title="Encumbrance Project Account")
	
	if (not doc.custom_encumbrance_material_request_account):
		form_link = get_link_to_form("Company", company)
		frappe.throw(f"Please set account of {form_link}", title="Encumbrance Material Request Account")

	return frappe._dict({
		"default_fund": doc.custom_default_fund,
		"default_designated_asset_fund_account": doc.custom_default_designated_asset_fund_account,
		"default_inventory_fund_account": doc.custom_default_inventory_fund_account,
		"default_inventory_asset_account": doc.custom_default_inventory_asset_account,
		"encumbrance_project_account": doc.custom_encumbrance_project_account,
		"encumbrance_material_request_account": doc.custom_encumbrance_material_request_account,
	})