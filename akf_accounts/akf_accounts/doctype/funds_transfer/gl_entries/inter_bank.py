import frappe

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.gl_structure import (
	get_gl_structure
)

def make_inter_bank_gl_entries(self):
	if(self.transaction_purpose=="Inter Bank"):
		create_gl_from_bank(self)
		create_gl_to_bank(self)

def create_gl_from_bank(self):
	args = get_gl_structure(self)
	args.update({
		'account': self.from_bank,
		# 'cost_center': self.from_cost_center,
		'against': self.from_bank,			
		'credit': self.transfer_amount,
		'credit_in_account_currency': self.transfer_amount,						
		'credit_in_transaction_currency': self.transfer_amount
	})
	doc = frappe.get_doc(args).insert(ignore_permissions=True)
	doc.submit()
 
def create_gl_to_bank(self):
	args = get_gl_structure(self)
	args.update({
		'account': self.to_bank,
		# 'cost_center': self.to_cost_center,
		'against': self.to_bank,			
		'debit': self.transfer_amount,
		'debit_in_account_currency': self.transfer_amount,
		'debit_in_transaction_currency': self.transfer_amount,
	})
	doc = frappe.get_doc(args).insert(ignore_permissions=True)
	doc.submit()


''' def get_bank_account(bank):
	account = frappe.db.get_value('Bank Account', bank, 'account')
	if(not account):
		frappe.throw(f'Please set company account of bank account <b>{bank}</b>', title='Missing Info')
	return account '''