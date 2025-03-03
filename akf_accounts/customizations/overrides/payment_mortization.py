import frappe
from frappe.utils import get_link_to_form, fmt_money
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_accounts.utils.accounts_defaults import get_company_defaults
""" 
1- make debit entry of equity/fund account. (e.g; Capital Stock - AKFP)
2- make credit entry of Inventory account. (e.g; Inventory fund account (IFA) - AKFP)
"""
# VALIDATIONS
def validate_donor_balance(self):
	if (hasattr(self, "custom_advance_payment_by_accounting_dimension")):
		if(self.custom_advance_payment_by_accounting_dimension):
			paid_amount = self.paid_amount
			donorBalance = sum(d.actual_balance for d in self.custom_program_details)
			if (paid_amount > donorBalance):
				frappe.throw(f"The paid amount: <b>{fmt_money(paid_amount)}</b> is exceeding available balance <b>{fmt_money(donorBalance)}</b>.", title="Insufficient Balance")

# GL ENTRY
def make_mortization_gl_entries(self):
	if (hasattr(self, "custom_advance_payment_by_accounting_dimension")):
		if (hasattr(self, "custom_transaction_type")):
			if (self.custom_transaction_type == "Asset Purchase"): make_asset_purchase_gl_entries(self)
			elif (self.custom_transaction_type == "Inventory Purchase Restricted"): make_inventory_gl_entries(self)

def get_gl_entry_dict(self):
	return frappe._dict({
		'doctype': 'GL Entry',
		'posting_date': self.posting_date,
		'transaction_date': self.posting_date,
		'against': f"Payment Entry: {self.name}",
		'against_voucher_type': 'Payment Entry',
		'against_voucher' : self.name,
		'voucher_type': 'Payment Entry',
		'voucher_subtype': 'Receive',
		'voucher_no': self.name,
		'company': self.company,
		'party_type': 'Supplier',
		'party': self.party
	})

def make_asset_purchase_gl_entries(self):
	def make_debit_material_request_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			'account': row.encumbrance_material_request_account,
			'debit': amount,
			'debit_in_account_currency': amount,
			"debit_in_transaction_currency": amount,
			"transaction_currency": row.currency,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def make_credit_designated_asset_fund_account(args, row, amount):
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
		accounts = get_company_defaults(self.company)
		itemBalance = self.paid_amount
		args = get_gl_entry_dict(self)
		for row in self.custom_program_details:
			args.update({
				"cost_center": row.pd_cost_center,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"donor": row.pd_donor,
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Advance supplier payment for puchase.',
			})

			balance_amount = row.actual_balance

			if(balance_amount<=itemBalance):
				# itemBalance = (7000 - 5000) = 2000
				itemBalance = (itemBalance - balance_amount)
				# gl entry
				make_debit_material_request_entry(args, row, balance_amount)
				make_credit_designated_asset_fund_account(args, row, balance_amount)

			elif(itemBalance>0 and balance_amount>itemBalance):
				# gl entry
				make_debit_material_request_entry(args, row, itemBalance)
				make_credit_designated_asset_fund_account(args, row, itemBalance)
				itemBalance = 0

	process_asset()
	success_msg()

def make_inventory_gl_entries(self):
	
	def debit_material_request_gl_entry(args, row, amount):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": row.encumbrance_material_request_account,
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
		
	def process_inventory():
		args = get_gl_entry_dict(self)
		itemBalance = self.paid_amount
		# looping
		for row in self.custom_program_details:
			args.update({
				"cost_center": row.pd_cost_center,
				"service_area": row.pd_service_area,
				"subservice_area": row.pd_subservice_area,
				"product": row.pd_product,
				"project": row.pd_project,
				"donor": row.pd_donor,
				"transaction_currency ": row.currency,
				"inventory_flag": 'Purchased',
				'remarks': 'Donation for item',
			})
			balance_amount = row.actual_balance

			if(balance_amount<=itemBalance):
				# itemBalance = (7000 - 5000) = 2000
				itemBalance = (itemBalance - balance_amount)
				# gl entry
				debit_material_request_gl_entry(args, row, balance_amount)
				credit_inventory_gl_entry(args, row, balance_amount)

			elif(itemBalance>0 and balance_amount>itemBalance):
				# gl entry
				debit_material_request_gl_entry(args, row, itemBalance)
				credit_inventory_gl_entry(args, row, itemBalance)
				itemBalance = 0
		
	process_inventory()
	success_msg()

def success_msg():
	frappe.msgprint("GL Entries created successfully!", alert=1)

# It will use on on_cancel() function.
def delete_all_gl_entries(self):
	if (hasattr(self, "custom_advance_payment_by_accounting_dimension")):
		if(frappe.db.exists("GL Entry", {"voucher_no": self.name})):
			frappe.db.sql("DELETE FROM `tabGL Entry` WHERE voucher_no = %s", self.name)