import frappe
from frappe.utils import getdate
from akf_accounts.utils.accounts_defaults import get_company_defaults
from erpnext.accounts.utils import get_company_default
from  akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from frappe.model.mapper import get_mapped_doc

def make_asset_movement_gl_entries(self):
	
	if (self.purpose != "Transfer"): 
		return
	
	if(not get_company_default(self.company, "custom_enable_asset_accounting", ignore_validation=True)): 
		return
	
	def credit_default_asset_account(args, row):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.default_asset_account,
		})
		total_asset_cost = row.total_asset_cost
		if(self.add_to_transit):
			args.update({
				"cost_center": row.source_cost_center,
				"credit": total_asset_cost,
				"credit_in_account_currency": total_asset_cost,
				"credit_in_transaction_currency": total_asset_cost,
			})
		else:
			args.update({
				"cost_center": row.target_cost_center,
				"debit": total_asset_cost,
				"debit_in_account_currency": total_asset_cost,
				"debit_in_transaction_currency": total_asset_cost,
			})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		
	def debit_default_designated_asset_fund_account(args, row):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.default_designated_asset_fund_account,
		})
		total_asset_cost = row.total_asset_cost
		if(self.add_to_transit):
			args.update({
				"cost_center": row.source_cost_center,
				"debit": total_asset_cost,
				"debit_in_account_currency": total_asset_cost,
				"debit_in_transaction_currency": total_asset_cost,
			})
		else:
			args.update({
				"cost_center": row.target_cost_center,
				"credit": total_asset_cost,
				"credit_in_account_currency": total_asset_cost,
				"credit_in_transaction_currency": total_asset_cost,
			})
			
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def debit_accumulated_depreciation_account(args, row):
		if(not self.add_to_transit): return
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.accumulated_depreciation_account,
		})
		total_asset_cost = row.total_asset_cost
		args.update({
			"cost_center": row.source_cost_center,
			"debit": total_asset_cost,
			"debit_in_account_currency": total_asset_cost,
			"debit_in_transaction_currency": total_asset_cost,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

	def debit_asset_in_transit_account(args, row):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.asset_in_transit_account,
		})
		total_asset_cost = row.total_asset_cost
		if(self.add_to_transit):
			args.update({
				"cost_center": row.in_transit_cost_center,
				"debit": total_asset_cost,
				"debit_in_account_currency": total_asset_cost,
				"debit_in_transaction_currency": total_asset_cost,
			})
		else:
			args.update({
				"cost_center": row.in_transit_cost_center,
				"credit": total_asset_cost,
				"credit_in_account_currency": total_asset_cost,
				"credit_in_transaction_currency": total_asset_cost,
			})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def credit_designated_asset_in_transit_fund(args, row):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.designated_asset_in_transit_fund,
		})
		total_asset_cost = row.total_asset_cost
		if(self.add_to_transit):
			args.update({
				"cost_center": row.in_transit_cost_center,
				"credit": total_asset_cost,
				"credit_in_account_currency": total_asset_cost,
				"credit_in_transaction_currency": total_asset_cost,
			})
		else:
			args.update({
				"cost_center": row.in_transit_cost_center,
				"debit": total_asset_cost,
				"debit_in_account_currency": total_asset_cost,
				"debit_in_transaction_currency": total_asset_cost,
			})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

	def change_asset_location_and_cost_center(row):
		location = row.in_transit_location if(self.add_to_transit) else row.target_location
		frappe.db.set_value("Asset", row.asset, "location", location)
		cost_center = row.in_transit_cost_center if(self.add_to_transit) else row.target_cost_center
		frappe.db.set_value("Asset", row.asset, "cost_center", cost_center)

	def process_asset_movement():
		args = get_gl_entry_dict(self)
		for row in self.assets:
			credit_default_asset_account(args, row)
			debit_default_designated_asset_fund_account(args, row)
			debit_asset_in_transit_account(args, row)
			credit_designated_asset_in_transit_fund(args, row)
			# debit_default_asset_nbv_account(args, row.total_asset_cost, row.source_cost_center)
			debit_accumulated_depreciation_account(args, row)
			change_asset_location_and_cost_center(row)

	process_asset_movement()

def get_gl_entry_dict(self):
	return frappe._dict({
		'doctype': 'GL Entry',
		'posting_date': getdate(self.transaction_date),
		'transaction_date': getdate(self.transaction_date),
		'against': f"Asset Movement: {self.name}",
		'against_voucher_type': 'Asset Movement',
		'against_voucher': self.name,
		'voucher_type': 'Asset Movement',
		'voucher_no': self.name,
		'voucher_subtype': f'{self.purpose}, asset moved between branches. ',
		'company': self.company,
		# 'remarks': self.instructions_internal,
		# 'is_opening': 'No',
		# 'is_advance': 'No',
		# 'transaction_currency': self.currency,
		# 'transaction_exchange_rate': self.exchange_rate,
		# Accounting Dimensions
		# "donor": self.donor,
		# "service_area": self.program,
		# "subservice_area": self.subservice_area,
		# "product": self.product,
		# "cost_center": self.cost_center,
	})
	
# It will use on on_cancel() function.
def delete_all_gl_entries(self):
	if(not get_company_default(self.company, "custom_enable_asset_accounting", ignore_validation=True)): return
	if(frappe.db.exists("GL Entry", {"voucher_no": self.name})):
		frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)


# End Transit Process
@frappe.whitelist()
def make_asset_movement_end_transit_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.add_to_transit = 0
		target.reference_doctype = source.doctype
		target.reference_name = source.name
		# target.purpose = "Material Transfer"
		# target.set_missing_values()
		# target.make_serial_and_batch_bundle_for_transfer()

	def update_item(source_doc, target_doc, source_parent):
		pass
		# target_doc.t_warehouse = ""

		# if source_doc.material_request_item and source_doc.material_request:
		# 	add_to_transit = frappe.db.get_value("Stock Entry", source_name, "add_to_transit")
		# 	if add_to_transit:
		# 		warehouse = frappe.get_value(
		# 			"Material Request Item", source_doc.material_request_item, "warehouse"
		# 		)
		# 		target_doc.t_warehouse = warehouse

		# target_doc.s_warehouse = source_doc.t_warehouse
		# target_doc.qty = source_doc.qty - source_doc.transferred_qty

	doclist = get_mapped_doc(
		"Asset Movement",
		source_name,
		{
			"Asset Movement": {
				"doctype": "Asset Movement",
				# "field_map": {"name": "outgoing_stock_entry"},
				"validation": {"docstatus": ["=", 1]},
			},
			# "Stock Entry Detail": {
			# 	"doctype": "Stock Entry Detail",
			# 	"field_map": {
			# 		"name": "ste_detail",
			# 		"parent": "against_stock_entry",
			# 		"serial_no": "serial_no",
			# 		"batch_no": "batch_no",
			# 	},
			# 	"postprocess": update_item,
			# 	"condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty) > 0.01,
			# },
		},
		target_doc,
		set_missing_values,
	)

	return doclist

