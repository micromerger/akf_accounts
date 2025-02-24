import frappe
from frappe.utils import get_link_to_form
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
""" 
1- make debit entry of equity/fund account. (e.g; Capital Stock - AKFP)
2- make credit entry of Inventory account. (e.g; Inventory fund account (IFA) - AKFP)
"""
# VALIDATIONS
def validate_donor_balance(self):
	itemBalance = sum(d.amount for d in self.items)
	donorBalance = sum(d.actual_balance for d in self.program_details)
	if (itemBalance > donorBalance):
		frappe.throw("Insufficient Balance: The donated amount is less than the required amount.")

# STOCK LEDGER ENTRY
def update_stock_ledger_entry(self):
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
	if (hasattr(self, "custom_type_of_transaction")):
		if (self.custom_type_of_transaction == "Asset Purchase"): make_asset_purchase_gl_entries(self)
		elif (self.custom_type_of_transaction == "Inventory Purchase Restricted"): make_inventory_gl_entries(self)

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

	return frappe._dict({
		"default_fund": doc.custom_default_fund,
		"default_designated_asset_fund_account": doc.custom_default_designated_asset_fund_account,
		"default_inventory_fund_account": doc.custom_default_inventory_fund_account
	})

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
		'company': self.company,
	})

def make_asset_purchase_gl_entries(self):
	def make_default_fund(args, row, accounts, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			'account': accounts.default_fund,
			'debit': amount,
			'debit_in_account_currency': amount,
			"debit_in_transaction_currency": amount,
			"transaction_currency": row.currency,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def make_designated_asset_fund_account(args, row, accounts, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			'account': accounts.default_designated_asset_fund_account,
			'credit': amount,
			'credit_in_account_currency': amount,
			"credit_in_transaction_currency": amount,
			"transaction_currency": row.currency,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

	def start_asset():
		accounts = get_company_defaults(self.company)
		itemBalance = sum(d.amount for d in self.items) or 0.0
		args = get_gl_entry_dict(self)
		for row in self.program_details:
			args.update({
				"cost_center": row.pd_cost_center,
				"account": row.pd_account,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"donor": row.pd_donor,
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Donation for item',
			})
			actualBalance = row.actual_balance
			amount = itemBalance if(itemBalance<=actualBalance) else (itemBalance - actualBalance)
			itemBalance = itemBalance - amount
			# Create the GL entry for the debit account and update
			make_default_fund(args, row, accounts, amount)
			# Create the GL entry for the credit account and update
			make_designated_asset_fund_account(args, row, accounts, amount)
	
	start_asset()
	success_msg()

def make_inventory_gl_entries(self):
	def equity_debit_gl_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(args)
		args.update({
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
		
	def inventory_credit_gl_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(args)
		# get default inventory account
		accounts = get_company_defaults(self.company)
		args.update({
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
		
	def start_inventory():
		args = get_gl_entry_dict(self)
		itemBalance = sum(d.amount for d in self.items) or 0.0
		# looping
		for row in self.program_details:
			args.update({
				"cost_center": row.pd_cost_center,
				"account": row.pd_account,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"donor": row.pd_donor,
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Donation for item',
			})
			actualBalance = row.actual_balance 
			# amount = 20-10 = 10
			# amount = 10-10 = 0
			amount = itemBalance if(itemBalance<=actualBalance) else (itemBalance - actualBalance)
			itemBalance = itemBalance - amount
			if(itemBalance>0.0):
				# function #01
				equity_debit_gl_entry(args, row, amount)
				# function #01
				inventory_credit_gl_entry(args, row, amount)
		
	start_inventory()
	success_msg()

def success_msg():
	frappe.msgprint("GL Entries created successfully!", alert=1)

# It will use on on_cancel() function.
def delete_all_gl_entries(self):
	if(frappe.db.exists("GL Entry", {"voucher_no": self.name})):
		frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)