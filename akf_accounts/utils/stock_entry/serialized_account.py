
import frappe
from erpnext.accounts.utils import (
	get_company_default
)

'''
Process of add accounts detail while creating serial nos
'''
def add_serial_no_accounts(doc, method=None):
	if(get_company_default(doc.company, "custom_enable_accounting_dimensions_dialog", ignore_validation=True)): 
		if(doc.doctype == 'Stock Entry'):
			if(
				doc.docstatus==1 
				and doc.stock_entry_type == 'Material Receipt'
			):
				for row in doc.items:
					serial_no = frappe.db.get_value('Serial No', {'item_code': row.item_code, 'purchase_document_no': doc.name}, "name")	
					if(serial_no):
						filters = frappe._dict({
							"company": doc.company,
							"name": doc.name,
							"item_code": row.item_code,
							"equity_account": row.expense_account,
							"inventory_flag": row.inventory_flag,
						})
						update_serial_no_accounts(filters)
				
		elif(doc.doctype == 'Purchase Receipt'):
			if(doc.custom_program_details):
				equity_account = frappe.db.get_value('Program Details', {'parent': doc.name}, 'encumbrance_material_request_account')
				inventory_flag = "Purchased"
				for row in doc.items:
					serial_no = frappe.db.get_value('Serial No', {'item_code': row.item_code, 'purchase_document_no': doc.name}, "name")	
					if(serial_no):
						filters = frappe._dict({
							"company": doc.company,
							"name": doc.name,
							"item_code": row.item_code,
							"equity_account": equity_account,
							"inventory_flag": inventory_flag,
						})
						update_serial_no_accounts(filters)

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
			serial_and_batch_bundle = frappe.db.get_value('Serial and Batch Bundle',{'voucher_no':  doc.name}, 'name') if(not row.serial_and_batch_bundle) else None
			
			if(serial_and_batch_bundle):
				data = frappe.db.sql(f'''
					Select sn.custom_equity_account, sn.custom_income_account, sum(sb.incoming_rate) as total_amount, sum(sb.qty) total_qty, sn.purchase_document_no
					From `tabSerial and Batch Entry`  sb inner join `tabSerial No` sn on (sb.serial_no=sn.name)
					Where 
						sb.docstatus = 1
						and ifnull(sn.custom_equity_account,'')!=''
						and ifnull(sn.custom_income_account,'')!=''
						and sb.parent = '{serial_and_batch_bundle}'
					Group by
						sn.custom_equity_account, sn.custom_income_account, sb.incoming_rate, sn.purchase_document_no
				''', as_dict=1)
				
				for d in data:
					args = get_gl_structure(doc)
					
					# debit equity account
					cargs = get_currency_args()
					args.update(cargs)
					args.update({
						'remarks': 'accounts reversal.',
						'cost_center': row.cost_center,
						'debit': d.total_amount,
						'debit_in_account_currency': d.total_amount,
						'debit_in_transaction_currency': d.total_amount,
						'account': d.custom_equity_account
					})
					edoc = frappe.get_doc(args)
					edoc.insert(ignore_permissions=True)
					edoc.submit()
					
					# credit income account
					cargs = get_currency_args()
					args.update(cargs)
					args.update({
						'remarks': 'accounts reversal.',
						'cost_center': row.cost_center,
						'credit': d.total_amount,
						'credit_in_account_currency': d.total_amount,
						'credit_in_transaction_currency': d.total_amount,
						'account': d.custom_income_account
					})
					idoc = frappe.get_doc(args)
					idoc.insert(ignore_permissions=True)
					idoc.submit()
				

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
	return frappe._dict({
		# Company Currency
		"debit": 0,
		"credit": 0,
		# Account Currency
		"debit_in_account_currency": 0,
		"credit_in_account_currency": 0,
		# Transaction Currency
		"debit_in_transaction_currency": 0,
		"credit_in_transaction_currency": 0
	})
