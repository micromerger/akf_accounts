import frappe
from frappe.utils import get_link_to_form

def get_company_defaults(company):
	doc = frappe.get_doc("Company", company)  
	form_link = get_link_to_form("Company", company)

	if (not doc.custom_default_fund):
		frappe.throw(f"Please set account of {form_link}", title="Fund Account")
 	
	if (not doc.custom_default_designated_asset_fund_account):
		frappe.throw(f"Please set account of {form_link}", title="Designated Asset Fund Account")

	if (not doc.custom_default_inventory_fund_account):		
		frappe.throw(f"Please set account of {form_link}", title="Designated Inventory Fund Account")

	if (not doc.custom_encumbrance_project_account):
		frappe.throw(f"Please set account of {form_link}", title="Encumbrance Project Account")
	
	if (not doc.custom_encumbrance_material_request_account):
		frappe.throw(f"Please set account of {form_link}", title="Encumbrance Material Request Account")

	if (not doc.custom_encumbrance_purchase_order_account):
		frappe.throw(f"Please set account of {form_link}", title="Encumbrance Purchase Order Account")

	if (not doc.custom_default_stock_in_transit):
		frappe.throw(f"Please set account of {form_link}", title="Stock In Transit")
	
	if (not doc.default_inventory_account):
		frappe.throw(f"Please set account of {form_link}", title="Inventory Account")

	if (not doc.custom_default_inventory_asset_account):
		frappe.throw(f"Please set account of {form_link}", title="Inventory Asset Account")

	if (not doc.custom_designated_inventory_in_transit_fund):
		frappe.throw(f"Please set account of {form_link}", title="Designated Inventory In Transit Fund")

	if (not doc.custom_default_income):
		frappe.throw(f"Please set account of {form_link}", title="Default Income Account")

	return frappe._dict({
		"default_fund": doc.custom_default_fund,
		"default_designated_asset_fund_account": doc.custom_default_designated_asset_fund_account,
		# "default_inventory_asset_account": doc.custom_default_inventory_asset_account,
		"encumbrance_project_account": doc.custom_encumbrance_project_account,
		"encumbrance_material_request_account": doc.custom_encumbrance_material_request_account,
		"encumbrance_purchase_order_account": doc.custom_encumbrance_purchase_order_account,
		# Asset (In Transit)
		"default_stock_in_transit": doc.custom_default_stock_in_transit,
		"default_inventory_asset_account": doc.custom_default_inventory_asset_account,
		# Equity (In Transit)
		"designated_inventory_in_transit_fund": doc.custom_designated_inventory_in_transit_fund,
		"default_inventory_fund_account": doc.custom_default_inventory_fund_account,
		"default_inventory_account": doc.default_inventory_account,
		# Income (In Transit)
		"default_income": doc.custom_default_income,
	})