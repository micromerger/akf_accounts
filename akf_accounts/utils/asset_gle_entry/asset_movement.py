import frappe
from frappe.utils import getdate
from akf_accounts.utils.accounts_defaults import get_company_defaults
from  akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args

def make_asset_inventory_gl_entries(self):
	def credit_asset_stock_entry(args, default_inventory_asset_account):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": default_inventory_asset_account,
			"credit": self.gross_purchase_amount,
			# Account Currency
			"credit_in_account_currency": self.gross_purchase_amount,
			# Transaction Currency
			"credit_in_transaction_currency": self.gross_purchase_amount,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		
	def debit_equity_asset_entry(args, default_inventory_fund_account):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": default_inventory_fund_account,
			"debit": self.gross_purchase_amount,
			# Account Currency
			"debit_in_account_currency": self.gross_purchase_amount,
			# Transaction Currency
			"debit_in_transaction_currency": self.gross_purchase_amount,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def process_asset_movement():
		for row in self.assets:
			
	if(hasattr(self, "custom_against_stock_entry")):
		if(self.custom_against_stock_entry):
			accounts = get_company_defaults(self.company)
			args = get_gl_entry_dict(self)
			credit_asset_stock_entry(args, accounts.default_inventory_asset_account)
			debit_equity_asset_entry(args, accounts.default_inventory_fund_account)

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
		# 'remarks': self.instructions_internal,
		# 'is_opening': 'No',
		# 'is_advance': 'No',
		'company': self.company,
		# 'transaction_currency': self.currency,
		# 'transaction_exchange_rate': self.exchange_rate,
		# Accounting Dimensions
		# "donor": self.donor,
		# "service_area": self.program,
		# "subservice_area": self.subservice_area,
		# "product": self.product,
		# "cost_center": self.cost_center,
	})

	



