import frappe

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.gl_structure import (
	get_gl_structure
)

from akf_accounts.akf_accounts.doctype.funds_transfer.deduction_breakeven import (
    make_deduction_gl_entries
)

def make_inter_branch_gl_entries(self):
	if(self.transaction_purpose=="Inter Branch"):
		# if(self.from_gl_entry):
		for entry in get_from_gl_entries(self):
			gl_struct = get_gl_structure(self)
			create_gl_entry(gl_struct, entry)
		
		# if(self.to_gl_entry):
		for entry in get_to_gl_entries(self):
			gl_struct = get_gl_structure(self)
			create_gl_entry(gl_struct, entry)

		make_deduction_gl_entries(self)

def create_gl_entry(gl_struct, entry):
	gl_struct.update(entry)
	print(gl_struct)
	# Create GL Entry
	doc = frappe.get_doc(gl_struct)
	doc.flags.ignore_permissions = True
	doc.insert()
	doc.submit()

def get_from_gl_entries(self):
	gl_entries = []
	total_amount = 0
	for row in self.funds_transfer_from:
		credit_debit = row.outstanding_amount
		total_amount += credit_debit
		# Common fields in gl entry
		entry = {
				'against_voucher_type': 'Project',
				'against_voucher': row.project,
	
				'cost_center': self.from_cost_center,
				'donor': row.ff_donor,
				'donor_type': row.donor_type,
				'donor_desk': row.donor_desk,
				'donation_type': row.donation_type,
				'transaction_type': row.transaction_type,
				'project': row.project,
				'fund_class': row.fund_class,
				'service_area': row.ff_service_area,
				'subservice_area': row.ff_subservice_area,
				'product': row.ff_product,
			}

		# Main Equity-Account entry (DEBIT)
		main_entry = {
				'party_type': 'Donor',
				'party': row.ff_donor,
				'account': row.ff_account,
				'against': row.ff_account,
				'debit': row.ff_transfer_amount,
				'debit_in_account_currency': row.ff_transfer_amount,
				'debit_in_transaction_currency': row.ff_transfer_amount,
			}
		main_entry.update(entry)

		# IBFT_Equity entry (CREDIT)
		ibft_entry = {
			'party_type': 'Donor',
			'party': row.ff_donor,
			'account': self.ibft_equity_account,
			# 'cost_center': self.from_cost_center,
			'against': self.ibft_equity_account,
			'credit': credit_debit,
			'credit_in_account_currency': credit_debit,						
			'credit_in_transaction_currency': credit_debit,
		}

		ibft_entry.update(entry)
		
		# Bank desposit in transit account.
		desposit_entry = {
			'account': self.desposit_in_transit_account,
			# 'cost_center': self.from_cost_center,
			'against': self.desposit_in_transit_account,
			'debit': credit_debit,
			'debit_in_account_currency': credit_debit,
			'debit_in_account_currency': credit_debit,
			#
		}
		desposit_entry.update(entry)
		gl_entries += [main_entry, desposit_entry, ibft_entry]

	# Pass one gl of from-bank-account
	from_bank_entry = get_gl_from_bank_account(self, total_amount)
	
	gl_entries += [from_bank_entry]
	
	return gl_entries

def get_gl_from_bank_account(self, amount):
	return {
			'account': get_bank_account(self.from_bank_account),
			'cost_center': self.from_cost_center,
			'against': self.from_bank_account,			
			'credit': amount,
			'credit_in_account_currency': amount,						
			'credit_in_transaction_currency': amount
		}

def get_to_gl_entries(self):
	gl_entries = []
	total_amount = 0
	for row in self.funds_transfer_from:
		credit_debit = row.outstanding_amount
		total_amount += credit_debit
		# Common fields in gl entry
		entry = {
				
				'against_voucher_type': 'Project',
				'against_voucher': row.project,
				'donor': row.ff_donor,
				'donor_type': row.donor_type,
				'donor_desk': row.donor_desk,
				'donation_type': row.donation_type,
				'transaction_type': row.transaction_type,
				'project': row.project,
				'fund_class': row.fund_class,
				'service_area': row.ff_service_area,
				'subservice_area': row.ff_subservice_area,
				'product': row.ff_product,
			}

		# IBFT_Equity entry (debit)
		ibft_entry = {
			'party_type': 'Donor',
			'party': row.ff_donor,
			'account': self.ibft_equity_account,
			'cost_center': self.from_cost_center,
			'against': self.ibft_equity_account,
			'debit': credit_debit,
			'debit_in_account_currency': credit_debit,
			'debit_in_transaction_currency': credit_debit,
		}
		ibft_entry.update(entry)

		# Main Equity-Account entry
		main_entry = {
				'party_type': 'Donor',
				'party': row.ff_donor,
				'account': row.ff_account,
				'against': row.ff_account,
				'cost_center': self.to_cost_center,
				'credit': credit_debit,
				'credit_in_account_currency': credit_debit,						
				'credit_in_transaction_currency': credit_debit,
			}
		main_entry.update(entry)

		# Bank desposit in transit account (credit)
		desposit_entry = {
				'account': self.desposit_in_transit_account,
				'cost_center': self.from_cost_center,
				'against': self.desposit_in_transit_account,
				'credit': credit_debit,
				'credit_in_account_currency': credit_debit,
				'credit_in_transaction_currency': credit_debit,
				#
			}
		desposit_entry.update(entry)
		
		gl_entries += [main_entry, desposit_entry, ibft_entry]

	# Pass one gl of from-bank-account
	bank_entry = get_gl_to_bank_account(self, total_amount)
	
	gl_entries += [bank_entry]
	
	return gl_entries

def get_gl_to_bank_account(self, amount):
	return {
			'account': get_bank_account(self.to_bank_account),
			'cost_center': self.to_cost_center,
			'against': self.to_bank_account,			
			'debit': amount,
			'debit_in_account_currency': amount,
			'debit_in_transaction_currency': amount,
		}

def get_bank_account(bank):
	account = frappe.db.get_value('Bank Account', bank, 'account')
	if(not account):
		frappe.throw(f'Please set company account of bank account <b>{bank}</b>', title='Missing Info')
	return account
