import frappe
from frappe.utils import get_link_to_form
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_accounts.utils.accounts_defaults import get_company_defaults
from erpnext.accounts.utils import get_company_default
""" 
1- make debit entry of equity/fund account. (e.g; Capital Stock - AKFP)
2- make credit entry of Inventory account. (e.g; Inventory fund account (IFA) - AKFP)
"""
# VALIDATIONS
def validate_donor_balance(self):
	if(self.is_new()): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("custom_program_details", [])
		return
	itemBalance = sum(d.amount for d in self.items)
	# itemBalance = sum(d.price_list_rate for d in self.items)
	donorBalance = sum(d.actual_balance for d in self.custom_program_details)
	if (itemBalance > donorBalance):
		frappe.throw("Insufficient donor balance.")

# STOCK LEDGER ENTRY
def update_stock_ledger_entry(self):
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	for row in self.items:
		if(hasattr(row, "custom_new") and hasattr(row, "custom_used")):
			if(frappe.db.exists("Stock Ledger Entry", 
				{"docstatus": 1, "item_code": row.item_code, "warehouse": row.warehouse})
				):
				frappe.db.sql(f""" 
						update `tabStock Ledger Entry`
						set custom_new = {row.custom_new}, custom_used = {row.custom_used}
						where docstatus=1 
							and voucher_detail_no = '{row.name}'
							and item_code = '{row.item_code}'
							and warehouse = '{row.warehouse}'
					""")

# GL ENTRY
def make_mortization_gl_entries(self):
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	if (hasattr(self, "custom_type_of_transaction")):
		if (self.custom_type_of_transaction == "Asset Purchase"): make_asset_purchase_gl_entries(self)
		elif (self.custom_type_of_transaction == "Inventory Purchase Restricted"): make_inventory_gl_entries(self)

def get_gl_entry_dict(self):
	return frappe._dict({
		'doctype': 'GL Entry',
		'posting_date': self.posting_date,
		'transaction_date': self.posting_date,
		'against': f"Purchase Invoice: {self.name}",
		'against_voucher_type': 'Purchase Invoice',
		'against_voucher' : self.name,
		'voucher_type': 'Purchase Invoice',
		'voucher_subtype': 'Receive',
		'voucher_no': self.name,
	})

def make_asset_purchase_gl_entries(self):
	def make_debit_assets_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			# 'account': row.encumbrance_material_request_account,
			'account': row.encumbrance_purchase_order_account,
			'debit': amount,
			'debit_in_account_currency': amount,
			"debit_in_transaction_currency": amount,
			"transaction_currency": row.currency,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def make_credit_designated_asset_entry(args, row, amount):
		# accounts = get_company_defaults(self.company)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			'account': row.amortise_designated_asset_fund_account,
			'credit': amount,
			'credit_in_account_currency': amount,
			"credit_in_transaction_currency": amount,
			"transaction_currency": row.currency,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

	def process_asset():
		# accounts = get_company_defaults(self.company)
		advanceBalance = sum(d.allocated_amount for d in self.advances)
		itemBalance = sum(d.amount for d in self.items) or 0.0
		itemBalance = (itemBalance - advanceBalance)
		args = get_gl_entry_dict(self)
		for row in self.custom_program_details:
			fargs = frappe._dict({
				"party_type": "Supplier",
				"party": self.supplier,
				"company": self.company,			
				"cost_center": row.pd_cost_center,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"fund_class": row.pd_fund_class,
				"donor": row.pd_donor,
				# "account": row.amortise_inventory_fund_account,
			}) 
			args.update(fargs)
			args.update({
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Donation for item',
			})
			balanceAmount = row.actual_balance
			
			if(balanceAmount<=itemBalance):
				# itemBalance = (7000 - 5000) = 2000
				itemBalance = (itemBalance - balanceAmount)
				# gl entry
				make_debit_assets_entry(args, row, balanceAmount)
				make_credit_designated_asset_entry(args, row, balanceAmount)

			elif(itemBalance>0 and balanceAmount>itemBalance):
				# gl entry
				make_debit_assets_entry(args, row, itemBalance)
				make_credit_designated_asset_entry(args, row, itemBalance)
				itemBalance = 0
	
	process_asset()
	success_msg()

def make_inventory_gl_entries(self):
	def debit_inventory_gl_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			# "account": row.encumbrance_material_request_account,
			'account': row.encumbrance_purchase_order_account,
			# Company Currency
			"debit": amount,
			# Account Currency
			"debit_in_account_currency": amount,
			# Transaction Currency
			"debit_in_transaction_currency": amount
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		
	def credit_inventory_gl_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(cargs)
		# get default inventory account
		# accounts = get_company_defaults(self.company)
		args.update({
			"account": row.amortise_inventory_fund_account,
			# Company Currency
			"credit": amount,
			# Account Currency
			"credit_in_account_currency": amount,
			# Transaction Currency
			"credit_in_transaction_currency": amount,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		
	def procsess_inventory():
		args = get_gl_entry_dict(self)
		advanceBalance = sum(d.allocated_amount for d in self.advances)
		itemBalance = sum(d.amount for d in self.items) or 0.0
		itemBalance = (itemBalance - advanceBalance)
		# looping
		for row in self.custom_program_details:
			fargs = frappe._dict({
				"party_type": "Supplier",
				"party": self.supplier,
				"company": self.company,	
				"cost_center": row.pd_cost_center,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"fund_class": row.pd_fund_class,
				"donor": row.pd_donor,
				# "account": row.amortise_inventory_fund_account,
			}) 
			args.update(fargs)
			args.update({
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Donation for item',
			}) 
			balanceAmount = row.actual_balance
			
			if(balanceAmount<=itemBalance):
				# itemBalance = (7000 - 5000) = 2000
				itemBalance = (itemBalance - balanceAmount)
				# gl entry
				debit_inventory_gl_entry(args, row, balanceAmount)
				credit_inventory_gl_entry(args, row, balanceAmount)
			
			elif(itemBalance>0 and balanceAmount>itemBalance):
				# gl entry
				debit_inventory_gl_entry(args, row, itemBalance)
				credit_inventory_gl_entry(args, row, itemBalance)
				itemBalance = 0
				
		
	procsess_inventory()
	success_msg()

def success_msg():
	frappe.msgprint("GL Entries created successfully!", alert=1)

# It will use on on_cancel() function.
def delete_all_gl_entries(self):
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	if(frappe.db.exists("GL Entry", {"voucher_no": self.name})):
		frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)
  
def validate_mortization_through_payment_entry(fargs): 
	credit = frappe.db.get_value("GL Entry", fargs, "sum(credit)") or 0.0
	if(credit>0.0): return True
	else: return False

