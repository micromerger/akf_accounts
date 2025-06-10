import frappe
from frappe.utils import get_link_to_form, fmt_money
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from erpnext.accounts.utils import get_company_default

def validate_donor_balance(doc, method=None):
	self = doc
	if(self.is_new()): return
	
	if(not self.custom_encumbrance): return	

	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		self.set("custom_program_details", [])
		return

	donor_balance = sum([d.actual_balance for d in self.custom_program_details])
	item_amount = sum([d.amount for d in self.items])

	if(not self.custom_program_details):
		frappe.throw("Balance is required to proceed further.", title='Donor Balance')
	if(item_amount> donor_balance):
		frappe.throw(f"Item amount: <b>Rs.{fmt_money(item_amount)}</b> exceeding the available balance: <b>Rs.{fmt_money(donor_balance)}</b>.", title='Donor Balance')

def make_encumbrance_purchase_order_gl_entries(doc, method=None):
	self = doc
	if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): return
	validate_donor_balance(self)
	args = frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': self.transaction_date,
			'transaction_date': self.transaction_date,
			'against': f"{self.doctype}: {self.name}",
			'against_voucher_type': self.doctype,
			'against_voucher': self.name,
			'voucher_type': self.doctype,
			'voucher_no': self.name,
			'voucher_subtype': 'Receive',
			'remarks': f"Encumbrance of {self.doctype.lower()}, {self.supplier_name}",
			'is_opening': 'No',
			'is_advance': 'No',
			'company': self.company,
		})
	amount = sum([d.amount for d in self.items])
	for row in self.custom_program_details:
		difference_amount = amount if(row.actual_balance>=amount) else (amount - row.actual_balance)
		amount = amount - difference_amount
		make_debit_gl_entry(args, row, difference_amount)
		make_credit_gl_entry(self.company, args, row, difference_amount)

	frappe.msgprint("Funds moves from `Project` to `Purchase Order` successfully!", indicator="green", alert=1)

def make_debit_gl_entry(args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.encumbrance_material_request_account,
		'cost_center': row.pd_cost_center,
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'fund_class': row.pd_fund_class,
		'donor': row.pd_donor,
		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_credit_gl_entry(company, args, row, amount):
	cargs = get_currency_args()	
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.encumbrance_purchase_order_account,
		'cost_center': row.pd_cost_center,
		'service_area': row.pd_service_area,
		'subservice_area': row.pd_subservice_area,
		'product': row.pd_product,
		'project': row.pd_project,
		'fund_class': row.pd_fund_class,
		'donor': row.pd_donor,
		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()
	
def del_encumbrance_gl_entries(doc, method=None):
	self = doc
	if(frappe.db.exists('GL Entry', {'against_voucher': self.name})):
		frappe.db.sql(f""" Delete from `tabGL Entry` where against_voucher = '{self.name}' """)
