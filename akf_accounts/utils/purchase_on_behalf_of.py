import frappe
from frappe.utils import get_link_to_form, fmt_money
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from erpnext.accounts.utils import get_company_default

def validate_donor_balance(self):
	if(self.is_new()): return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("program_details", [])
		return

	donor_balance = sum([d.actual_balance for d in self.program_details])
	item_amount = sum([d.amount for d in self.items])

	if(not self.program_details):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(item_amount> donor_balance):
		frappe.throw(f"Item amount: <b>Rs.{fmt_money(item_amount)}</b> exceeding the available balance: <b>Rs.{fmt_money(donor_balance)}</b>.", title='Donor Balance')

def make_on_behalf_of_gl_entries(self):
	if(not self.on_behalf_of): 
		return
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		return
	args = frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.posting_date,
			'transaction_date': self.posting_date,
			'against': f"Purchase Invoice: {self.name}",
			'against_voucher_type': 'Purchase Invoice',
			'against_voucher': self.name,
			'voucher_type': 'Purchase Invoice',
			'voucher_no': self.name,
			'is_opening': 'No',
			'is_advance': 'No',
			'company': self.company,
		})
	amount = sum([d.amount for d in self.items])
	for row in self.program_details:
		difference_amount = amount if(row.actual_balance>=amount) else (amount - row.actual_balance)
		amount = amount - difference_amount
		make_branchB_expense_gl_entry(self, args, row, difference_amount)
		make_branchB_equity_gl_entry(self, args, row, difference_amount)
		make_branchB_income_gl_entry(self, args, row, difference_amount)
		make_branchB_receivalbe_gl_entry(self, args, row, difference_amount)
		make_branchA_payable_gl_entry(self, args, row, difference_amount)

def make_branchB_expense_gl_entry(self, args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'voucher_subtype': 'Expense',
		'remarks': f"Branch 'A' purchasing on behalf of Branch 'B'.",
		# 'party_type': 'Donor',
		# 'party': row.pd_donor,
		'account': self.expense_account,
		'cost_center': self.purchasing_branch,
		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'donor': row.pd_donor,

		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_branchB_equity_gl_entry(self, args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'voucher_subtype': 'Equity',
		'remarks': f"Branch 'A' purchasing on behalf of Branch 'B'.",
		# 'party_type': 'Donor',
		# 'party': row.pd_donor,
		'account': self.equity_account,
		'cost_center': self.purchasing_branch,
		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'donor': row.pd_donor,
	})
	# debit entry
	args.update({'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

	# credit entry
	args.update({'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_branchB_income_gl_entry(self, args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'voucher_subtype': 'Equity',
		'remarks': f"Branch 'A' purchasing on behalf of Branch 'B'.",
		# 'party_type': 'Donor',
		# 'party': row.pd_donor,
		'account': self.income_account,
		'cost_center': self.purchasing_branch,
		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'donor': row.pd_donor,

		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_branchB_receivalbe_gl_entry(self, args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'voucher_subtype': 'Equity',
		'remarks': f"Branch 'A' purchasing on behalf of Branch 'B'.",
		'party_type': 'Customer',
		'party': self.receiving_customer,
		'account': self.inter_branch_receivable_account,
		'cost_center': self.purchasing_branch,
		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'donor': row.pd_donor,

		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_branchA_payable_gl_entry(self, args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'voucher_subtype': 'Equity',
		'remarks': f"Branch 'A' purchasing on behalf of Branch 'B'.",
		'party_type': 'Supplier',
		'party': self.purchasing_supplier,
		'account': self.inter_branch_payable_account,
		'cost_center': self.receiving_branch,
		
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'donor': row.pd_donor,

		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()
 
# def cancel_encumbrance_material_request_gl_entries(self):
# 	if(frappe.db.exists('GL Entry', {'against_voucher': self.name})):
# 		frappe.db.sql(f""" Delete from `tabGL Entry` where against_voucher = '{self.name}' """)
