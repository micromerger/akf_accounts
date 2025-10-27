import frappe
from frappe.utils import fmt_money
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from erpnext.accounts.utils import get_company_default
from akf_accounts.utils.accounts_defaults import (
	get_company_defaults
)
stock_entry_type_list = ['Material Issue', 'Inventory to Asset']

def validate_donor_balance(doc, method=None):
	self = doc

	if(self.stock_entry_type in stock_entry_type_list): 
		
		if(self.custom_program_details):

			if(not get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
				self.set("custom_program_details", [])
				return

			donor_balance = sum([d.actual_balance for d in self.custom_program_details])
			item_amount = sum([d.amount for d in self.items])

			if(not self.custom_program_details):
				frappe.throw("Balance is required to proceed further.", title='Donor Balance')
			
			if(item_amount> donor_balance):
				frappe.throw(f"Item amount: <b>Rs.{fmt_money(item_amount)}</b> exceeding the available balance: <b>Rs.{fmt_money(donor_balance)}</b>.", title='Donor Balance')

def make_mortizations_gl_entries(doc, method=None):
	self = doc
	if(self.stock_entry_type in stock_entry_type_list): 
		if(get_company_default(self.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
			validate_donor_balance(self)
			update_accounting_dimensions(self)
			args = frappe._dict({
				'doctype': 'GL Entry',
				'posting_date': self.posting_date,
				'transaction_date': self.posting_date,
				'against': f"{self.doctype}: {self.name}",
				'against_voucher_type': self.doctype,
				'against_voucher': self.name,
				'voucher_type': self.doctype,
				'voucher_no': self.name,
				'voucher_subtype': 'Receive',
				'remarks': f"Morization of {self.doctype}, {self.stock_entry_type}",
				'is_opening': 'No',
				'is_advance': 'No',
				'company': self.company,
			})
			
			amount = sum([d.amount for d in self.items])
			# Looping
			accounts = get_company_defaults(self.company)
			for row in self.custom_program_details:
				difference_amount = amount if(row.actual_balance>=amount) else (amount - row.actual_balance)
				amount = amount - difference_amount

				restricted_income_account_gl_entry(args, row, difference_amount, accounts.default_income if(doc.stock_entry_type=="Material Issue") else accounts.default_designated_asset_fund_account)
				material_request_encumbrance_debit_gl_entry(args, row, difference_amount) # debit
				# make_inventory_account_gl_entry(self.company, args, row, difference_amount, accounts.default_inventory_fund_account) # credit
				# restricted_expense_account_gl_entry(args, row, difference_amount, accounts.restricted_expense_account)

def restricted_income_account_gl_entry(args, row, amount, default_income):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': default_income, # Restricted Income 

		"project" : row.pd_project,
		"fund_class" : row.pd_fund_class,
		"service_area" : row.pd_service_area,
		"subservice_area" : row.pd_subservice_area,
		"product" : row.pd_product,
		"donor" : row.pd_donor,			
		"donor_desk" : row.pd_donor_desk,
		"donor_type" : row.pd_donor_type,
		"donation_type" : row.pd_intention,
		"cost_center" : row.pd_cost_center,
		"transaction_type" : row.pd_transaction_type,
		
		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def material_request_encumbrance_debit_gl_entry(args, row, amount):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': row.encumbrance_material_request_account,
		
		"project" : row.pd_project,
		"fund_class" : row.pd_fund_class,
		"service_area" : row.pd_service_area,
		"subservice_area" : row.pd_subservice_area,
		"product" : row.pd_product,
		"donor" : row.pd_donor,			
		"donor_desk" : row.pd_donor_desk,
		"donor_type" : row.pd_donor_type,
		"donation_type" : row.pd_intention,
		"cost_center" : row.pd_cost_center,
		"transaction_type" : row.pd_transaction_type,
		
		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def make_inventory_account_gl_entry(company, args, row, amount, default_inventory_fund_account):
	cargs = get_currency_args()	
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': default_inventory_fund_account,
  
		"project" : row.pd_project,
		"fund_class" : row.pd_fund_class,
		"service_area" : row.pd_service_area,
		"subservice_area" : row.pd_subservice_area,
		"product" : row.pd_product,
		"donor" : row.pd_donor,			
		"donor_desk" : row.pd_donor_desk,
		"donor_type" : row.pd_donor_type,
		"donation_type" : row.pd_intention,
		"cost_center" : row.pd_cost_center,
		"transaction_type" : row.pd_transaction_type,
		
  
		'credit': amount,
		'credit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'credit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def restricted_expense_account_gl_entry(args, row, amount, restricted_expense_account):
	cargs = get_currency_args()
	args.update(cargs)
	args.update({
		'party_type': 'Donor',
		'party': row.pd_donor,
		'account': restricted_expense_account,

		"project" : row.pd_project,
		"fund_class" : row.pd_fund_class,
		"service_area" : row.pd_service_area,
		"subservice_area" : row.pd_subservice_area,
		"product" : row.pd_product,
		"donor" : row.pd_donor,			
		"donor_desk" : row.pd_donor_desk,
		"donor_type" : row.pd_donor_type,
		"donation_type" : row.pd_intention,
		"cost_center" : row.pd_cost_center,
		"transaction_type" : row.pd_transaction_type,

		'debit': amount,
		'debit_in_account_currency': amount,
		'transaction_currency': row.currency,
		'debit_in_transaction_currency': amount,
	})
	doc = frappe.get_doc(args)
	doc.insert(ignore_permissions=True)
	doc.submit()

def update_accounting_dimensions(doc):
	if(doc.custom_program_details):
		for row in doc.custom_program_details:
			frappe.db.sql(f'''
					Update `tabGL Entry`
					Set 
						cost_center='{row.pd_cost_center}',	
						fund_class='{row.pd_fund_class}',
						project='{row.pd_project}',
						service_area='{row.pd_service_area}',
						subservice_area='{row.pd_subservice_area}',
						product='{row.pd_product}',
						donor = '{row.pd_donor}'
					Where
						voucher_no='{doc.name}'
					''')
	# else:
		

def del_stock_gl_entries(doc, method=None):
	self = doc
	if(self.stock_entry_type in stock_entry_type_list):
		if(self.custom_program_details):
			if(frappe.db.exists('GL Entry', {'against_voucher': self.name})):
				frappe.db.sql(f""" Delete from `tabGL Entry` where against_voucher = '{self.name}' """)
