import frappe

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.gl_structure import (
	get_gl_structure
)

def make_inter_fund_class_gl_entries(self):
	if(self.transaction_purpose=='Inter Fund' and self.transfer_type=='Fund Class'):
		gl_entries = get_gl_entries(self)
		
		for entry in gl_entries:
			gl_struct = get_gl_structure(self)
			create_gl_entry(gl_struct, entry)
			
		self.reload()

def create_gl_entry(gl_struct, entry):
	gl_struct.update(entry)
	# Create GL Entry
	doc = frappe.get_doc(gl_struct)
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()

def get_gl_entries(self):
	gl_entries = []

	for row in self.funds_transfer_from:
		credit_debit = row.ff_transfer_amount
		entry = {

				'account': row.ff_account,
				'against': row.ff_account,

				'party_type': 'Donor',
				'party': row.ff_donor,
				
				'cost_center': row.ff_cost_center,
				'donor': row.ff_donor,
				'donor_type': row.donor_type,
				'donor_desk': row.donor_desk,
				'donation_type': row.donation_type,
				'transaction_type': row.transaction_type,
				
				'service_area': row.ff_service_area,
				'subservice_area': row.ff_subservice_area,
				'product': row.ff_product,
				
			}
		debit_entry = {
				'against_voucher_type': 'Project',
				'against_voucher': row.project,
				'project': row.project,
				'fund_class': row.fund_class,
				
				'debit': credit_debit,
				'debit_in_account_currency': credit_debit,
				'debit_in_transaction_currency': credit_debit,
			}
		debit_entry.update(entry)

		credit_entry = {
				'against_voucher_type': 'Fund Class',
				'against_voucher': row.fund_class,

				'project': '',
				'fund_class': row.fund_class,
				
				'credit': credit_debit,
				'credit_in_account_currency': credit_debit,
				'credit_in_transaction_currency': credit_debit,
			}
		credit_entry.update(entry)
		
		gl_entries += [debit_entry, credit_entry]

	return gl_entries
