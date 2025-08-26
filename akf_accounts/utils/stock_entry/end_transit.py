import frappe 
from akf_accounts.utils.accounts_defaults import get_company_defaults
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args

def end_transit_gl_entries(self, args, accounts):
	def credit_stock_in_transit(source_cost_center):
		# Create the GL entry for the debit account and update
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
				"account": accounts.default_stock_in_transit,
				"cost_center": source_cost_center,			
				"credit": self.total_incoming_value,
				"credit_in_account_currency": self.total_incoming_value,
			})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def debit_designated_inventory_in_transit_fund(target_cost_center):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
				"account": accounts.designated_inventory_in_transit_fund,
				"cost_center": target_cost_center,			
				"debit": self.total_incoming_value,
				"debit_in_account_currency": self.total_incoming_value,
			})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def debit_default_inventory_account(target_cost_center):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": accounts.default_inventory_account,
			"cost_center": target_cost_center,			
			"debit": self.total_incoming_value,
			"debit_in_account_currency": self.total_incoming_value,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def credit_default_inventory_fund_account(target_cost_center):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": accounts.default_inventory_fund_account,
			"cost_center": target_cost_center,			
			"credit": self.total_incoming_value,
			"credit_in_account_currency": self.total_incoming_value,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()
  
	def start_process():
		for row in self.items:
			source_cost_center = frappe.db.get_value("Warehouse", row.s_warehouse, "custom_cost_center")
			target_cost_center = frappe.db.get_value("Warehouse", row.t_warehouse, "custom_cost_center")
			args.update({
				"service_area": row.service_area_id,
				"subservice_area": row.subservice_area_id,
				"product": row.product_id,
				"project": row.custom_target_project,
			})
			credit_stock_in_transit(source_cost_center)
			debit_designated_inventory_in_transit_fund(source_cost_center)
			debit_default_inventory_account(target_cost_center)
			credit_default_inventory_fund_account(target_cost_center)

	start_process()
