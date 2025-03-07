import frappe
from frappe.utils import get_link_to_form
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_accounts.utils.accounts_defaults import get_company_defaults

def validate_donor_balance(self):
	if(self.is_new()): return

	donor_balance = sum([d.actual_balance for d in self.program_details])
	item_amount = sum([d.amount for d in self.items])

	if(not self.program_details):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(item_amount> donor_balance):
		frappe.throw("Item amount exceeding the available donor balance.", title='Items')

# def get_company_defaults(company):
# 	temporary_project_fund_account = frappe.db.get_value("Company", company, "custom_default_temporary_project_fund_account")
# 	if(not temporary_project_fund_account):
# 		companylink = get_link_to_form("Company", company)
# 		frappe.throw(f""" Please set `Temporary Project Fund Account`. {companylink}""", title='Company')
# 	return temporary_project_fund_account

def make_funds_gl_entries(self):
	args = frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.transaction_date,
			'transaction_date': self.transaction_date,
			'against': f"Material Request: {self.name}",
			'against_voucher_type': 'Material Request',
			'against_voucher': self.name,
			'voucher_type': 'Material Request',
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			# 'remarks': self.instructions_internal,
			# 'is_opening': 'No',
			# 'is_advance': 'No',
			'company': self.company,
			# 'transaction_currency': self.currency,
			# 'transaction_exchange_rate': self.exchange_rate,
		})
	amount = sum([d.amount for d in self.items])
	for row in self.program_details:
		difference_amount = amount if(row.actual_balance>=amount) else (amount - row.actual_balance)
		amount = amount - difference_amount
		make_normal_equity_gl_entry(args, row, difference_amount)
		make_temporary_equity_gl_entry(self.company, args, row, difference_amount)

def make_normal_equity_gl_entry(args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.pd_account,
		'cost_center': row.pd_cost_center,
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

def make_temporary_equity_gl_entry(company, args, row, amount):
	cargs = get_currency_args()	
	args.update(cargs)
	accounts = get_company_defaults(company)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': accounts.encumbrance_material_request_account,
		'cost_center': row.pd_cost_center,
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
	# =>
	frappe.db.set_value('Program Details', row.name, 'temporary_account', encumbrance_material_request_account)
	
def cancel_gl_entry(self):
	if(frappe.db.exists('GL Entry', {'against_voucher': self.name})):
		frappe.db.sql(f""" Delete from `tabGL Entry` where against_voucher = '{self.name}' """)
	