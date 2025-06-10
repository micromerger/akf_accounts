import frappe
from frappe.model.mapper import get_mapped_doc
from frappe.utils import (get_link_to_form, getdate, fmt_money)
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_accounts.utils.accounts_defaults import get_company_defaults
from erpnext.accounts.utils import get_company_default

# VALIDATION ################################
def validate_donor_balance(doc, method=None):
	self = doc
	if(self.is_new()): return
	if(not self.fund_class): return
	if(not self.custom_program_details): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("custom_program_details", [])
		return
	accountsBalance = self.estimated_costing or 0.0
	donorBalnce = sum([d.actual_balance for d in self.custom_program_details]) or 0.0

	if(donorBalnce<=0.0):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(accountsBalance>donorBalnce):
		frappe.throw(f"Budget amount <b>Rs.{fmt_money(accountsBalance)}</b> exceeding the available balance <b>Rs.{fmt_money(donorBalnce)}</b>.", title='Budget Accounts')

# GL ENTRIES ################################
def make_project_encumbrance_gl_entries(doc, method=None):
	self = doc
	if(self.fund_class in ["", None]): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	# consumed amount
	consumed_amount = self.estimated_costing or 0.0
	# looping for gl entry
	for row in self.custom_program_details:
		balance_amount = row.actual_balance
		
		if(balance_amount<=consumed_amount):
			# consumed_amount = (7000 - 5000) = 2000
			consumed_amount = (consumed_amount - balance_amount)
			# gl entry
			make_debit_normal_equity_account(self, row, balance_amount)
			make_credit_temporary_encumbrance_project(self, row, balance_amount)

		elif(consumed_amount>0 and balance_amount>consumed_amount):
			# gl entry
			make_debit_normal_equity_account(self,  row, consumed_amount)
			make_credit_temporary_encumbrance_project(self, row, consumed_amount)
			consumed_amount = 0
	
	frappe.msgprint("Funds transfers from `Fund Class` to project success...", indicator="green", alert=1)

def get_args(self):
	posting_date = getdate()
	return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': posting_date,
			'transaction_date': posting_date,
			'against': f"Project: {self.name}",
			'against_voucher_type': "Fund Class",
			'against_voucher': self.fund_class,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			'remarks': f"Project: Encumbrance of project: {self.name} on {self.expected_start_date}",
			'is_opening': 'No',
			'is_advance': 'No',
			'company': self.company,
		})

def make_debit_normal_equity_account(self, row, amount):
	args = get_args(self)
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.pd_account,
		'cost_center': row.pd_cost_center,
		'fund_class': self.fund_class,	
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		# 'project': self.name,
		'donor': row.pd_donor,
		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	# frappe.throw(frappe.as_json(doc))
	doc.insert(ignore_permissions=True)
	
	doc.submit()

def make_credit_temporary_encumbrance_project(self, row, amount):
	args = get_args(self)
	cargs = get_currency_args()	
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.encumbrance_project_account,
		'cost_center': row.pd_cost_center,
		'fund_class': self.fund_class,		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': self.name,
		'donor': row.pd_donor,
		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()
	
def cancel_project_encumbrance_gl_entries(doc, method=None):
	self = doc
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	if(frappe.db.exists('GL Entry', {'voucher_no': self.name})):
		frappe.db.sql(f""" Delete from `tabGL Entry` where voucher_no = '{self.name}' """)


@frappe.whitelist()
def make_material_request(source_name, target_doc=None, args=None):
	# if args is None:
	# 	args = {}
	# if isinstance(args, str):
	# 	args = json.loads(args)

	def set_missing_values(source, target):
		doc = frappe.get_doc(target)
		doc.budget = source.name
		doc.encumbrance = source.encumbrance
	# 	if frappe.flags.args and frappe.flags.args.default_supplier:
	# 		# items only for given default supplier
	# 		supplier_items = []
	# 		for d in target_doc.items:
	# 			default_supplier = get_item_defaults(d.item_code, target_doc.company).get("default_supplier")
	# 			if frappe.flags.args.default_supplier == default_supplier:
	# 				supplier_items.append(d)
	# 		target_doc.items = supplier_items

	# 	set_missing_values(source, target_doc)

	# def select_item(d):
	# 	filtered_items = args.get("filtered_children", [])
	# 	child_filter = d.name in filtered_items if filtered_items else True

	# 	return d.ordered_qty < d.stock_qty and child_filter

	doclist = get_mapped_doc(
		"Budget",
		source_name,
		{
			"Budget": {
				"doctype": "Material Request",
				# "validation": {"docstatus": ["=", 1], "material_request_type": ["=", "Purchase"]},
			},
				"Program Details": {
				"doctype": "Program Details",
				# "field_map": [
				# 	["name", "material_request_item"],
				# 	["parent", "material_request"],
				# 	["uom", "stock_uom"],
				# 	["uom", "uom"],
				# 	["sales_order", "sales_order"],
				# 	["sales_order_item", "sales_order_item"],
				# 	["wip_composite_asset", "wip_composite_asset"],
				# ],
				# "postprocess": update_item,
				# "condition": select_item,
			},
		},
		target_doc,
		set_missing_values,
	)

	# doclist.set_onload("load_after_mapping", False)
	return doclist