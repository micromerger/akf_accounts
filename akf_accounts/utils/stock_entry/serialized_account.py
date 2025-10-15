
import frappe
from erpnext.accounts.utils import (
    get_company_default
)

'''
Process of add accounts detail while creating serial nos
'''
def add_serial_no_accounts(doc, method=None):
	if(get_company_default(doc.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		if(
			doc.docstatus==1 
			and doc.stock_entry_type == 'Material Receipt'
		):
			for row in doc.items:
				serial_no = frappe.db.get_value('Serial No', {'item_code': row.item_code, 'purchase_document_no': doc.name}, "name")	
				if(serial_no):
					equity_account = None
					inventory_flag = None
					execution_flag = False
					if(doc.doctype == 'Stock Entry'):
						equity_account = row.expense_account
						inventory_flag = row.inventory_flag
						execution_flag = True
					elif(doc.doctype == 'Purchase Receipt'):
						equity_account = frappe.db.get_value('Program Details', {'parent': doc.name}, 'encumbrance_material_request_account')
						inventory_flag = "Purchased"
						if(equity_account): 
							execution_flag = True 
					if(execution_flag):
						filters = frappe._dic({
							"company": doc.company,
							"name": doc.name,
							"item_code": row.item_code,
							"equity_account": equity_account,
							"inventory_flag": inventory_flag,
						})
						update_serial_no_accounts(filters)
			doc.reload()

def update_serial_no_accounts(filters):
	default_income_account = get_default_income_account(filters.get("company"))
	filters.update({
		'default_income_account': default_income_account
	})
	frappe.db.sql('''
		Update `tabSerial No`
		Set 
			custom_equity_account = %(equity_account)s,
			custom_income_account = %(default_income_account)s,
			custom_inventory_flag = %(inventory_flag)s
		Where
			item_code = %(item_code)s
			and purchase_document_no = %(name)s
	''', filters)
	
def get_default_income_account(company):
	default_income = frappe.db.get_value('Company', company, 'custom_default_income')
	if(not default_income):
		frappe.throw(f'Please set default income account of {company}', title='Missing Info')
	return default_income

'''
Process of consumption of item while transfer, asset, issuance.
'''
def make_gl_entry_of_serial_no_accounts(doc, method=None):
	if(
		doc.docstatus==1 
		and doc.stock_entry_type in ['Material Transfer', 'Material Issue', 'Inventory to Asset', 'Inventory Consumption - Restricted']
	):
		
		for row in doc.items:
			serial_batch_bundle = frappe.db.get_value('Serial and Batch Bundle', {'item_code': row.item_code, 'voucher_no': doc.name},'name')
			if(serial_batch_bundle):
				
				serail_doc = frappe.get_doc('Serial and Batch Bundle', serial_batch_bundle)
				serial_expense_account = None
				serial_income_account = None
				purchase_document_no = None

				for entry in serail_doc.entries:
					serial = frappe.db.get_value('Serial No', entry.serial_no, ['custom_equity_account', 'custom_income_account', 'purchase_document_no'], as_dict=1)
					if(serial):
						if(hasattr(row, 'custom_serial_expense_account')):
							serial_expense_account = serial.custom_equity_account
						if(hasattr(row, 'custom_serial_income_account')):
							serial_income_account = serial.custom_income_account
						
						purchase_document_no = serial.purchase_document_no
				
				dimensions = frappe.db.get_value('Stock Ledger Entry', {'voucher_no': purchase_document_no, 'warehouse': row.s_warehouse}, 
                        ['fund_class', 'service_area', 'subservice_area', 'product', 'cost_center', 'project', 'donor', 'donor_type', 'donor_desk', 'donation_type', 'transaction_type', 'inventory_flag'], 
                as_dict=1)

				args = get_gl_structure(doc)
				args.update(dimensions)
				# Serial Income Account [Cr]
				cargs = get_currency_args()
				args.update(cargs)
				args.update({
					'account': serial_income_account,
					'against': f"{serial_income_account}",
					"credit": row.amount,
					"credit_in_account_currency": row.amount,
					"credit_in_transaction_currency": row.amount
				})
				gl_doc = frappe.get_doc(args)
				gl_doc.flags.ignore_permissions = True
				gl_doc.insert()
				gl_doc.submit()

				# serial expense account
				cargs = get_currency_args()
				args.update(cargs)
				args.update({
					'account': serial_expense_account,
					'against': f"{serial_expense_account}",
					"debit": row.amount,
					"debit_in_account_currency": row.amount,
					"debit_in_transaction_currency": row.amount
				})
				gl_doc = frappe.get_doc(args)
				gl_doc.flags.ignore_permissions = True
				gl_doc.insert()
				gl_doc.submit()
				

				frappe.db.set_value('Stock Ledger Entry', {'voucher_no': doc.name}, dimensions)
				frappe.db.set_value('GL Entry', {'voucher_no': doc.name}, dimensions)

				# update stock entry details table name items
				dimensions.update({
					'custom_serial_income_account': serial_income_account,
					'custom_serial_expense_account': serial_expense_account
				})
				# print(dimensions)
				frappe.db.set_value('Stock Entry Detail', row.name, dimensions)

def get_gl_structure(doc):
	return frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': doc.posting_date,
			'transaction_date': doc.posting_date,
			# 'against_voucher_type': doc.doctype,
			# 'against_voucher': doc.name,
			'voucher_type': doc.doctype,
			'voucher_no': doc.name,
			'voucher_subtype': doc.stock_entry_type,
			'remarks': 'Stock Movement',
			# 'is_opening': 'No',
			# 'is_advance': 'No',
			'company': doc.company,
			# 'transaction_currency': doc.currency,
			# 'transaction_exchange_rate': doc.exchange_rate,
		})

def get_currency_args():
	return {
		# Company Currency
		"debit": 0,
		"credit": 0,
		# Account Currency
		"debit_in_account_currency": 0,
		"credit_in_account_currency": 0,
		# Transaction Currency
		"debit_in_transaction_currency": 0,
		"credit_in_transaction_currency": 0
	}