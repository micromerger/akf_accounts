import frappe
# import json

from akf_accounts.akf_accounts.doctype.funds_transfer.gl_entries.gl_structure import (
    get_gl_structure
)

# bench --site al-khidmat.com execute akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.make_project_inter_fund_gl_entries
def make_inter_fund_project_gl_entries(self):
	if(self.transaction_purpose=='Inter Fund' and self.transfer_type=='Project'):
		gl_entries = get_gl_entries(self)
		for entry in gl_entries:
			gl_struct = get_gl_structure(self)
			gl_struct.update(entry)
			# Create GL Entry
			doc = frappe.get_doc(gl_struct)
			doc.flags.ignore_permissions = True
			doc.insert()
			doc.submit()
		self.reload()
  
def get_gl_entries(self):
	# doc = frappe.get_doc('Funds Transfer', 'ntmbah8mi9')
	# self = doc
	funds_transfer_to = self.funds_transfer_to
	funds_transfer_from = self.funds_transfer_from
	
	gl_entries = []

	for row1 in funds_transfer_to:
		to_amount = row1.ft_amount

		for row2 in funds_transfer_from:
			from_amount = row2.ff_balance_amount
			credit_debit = 0
		
			if((to_amount > 0 and from_amount > 0) and (from_amount <= to_amount)):
				credit_debit = row2.ff_balance_amount
				# make transfer amount to zero
				row2.ff_balance_amount = 0
				to_amount = (to_amount - from_amount)
			
			elif(from_amount > to_amount):
				credit_debit = to_amount
				# remaining transfer amount
				row2.ff_balance_amount = (from_amount - to_amount)
				to_amount = 0

			if(credit_debit > 0):
				same_dict = {
					
					'account': row2.ff_account,
					'against': row2.ff_account,
					'party_type': 'Donor',
					'party': row2.ff_donor,
					'cost_center': row2.ff_cost_center,
					'donor': row2.ff_donor,
					'donor_type': row2.donor_type,
					'donor_desk': row2.donor_desk,
					'donation_type': row2.donation_type,
					'transaction_type': row2.transaction_type,
				}
				# Start Transfer To Dict
				transfer_to_dict =  {
					'against_voucher_type': 'Project',
					'against_voucher': row1.project,
						
					'project': row1.project,
					'fund_class': row1.fund_class,
					'service_area': row1.ft_service_area,
					'subservice_area': row1.ft_subservice_area,
					'product': row1.ft_product,
					'credit': credit_debit,
					'credit_in_account_currency': credit_debit,
					'credit_in_transaction_currency': credit_debit,
				}
				transfer_to_dict.update(same_dict)
				# End Transfer To Dict

				# Start Transfer From Dict
				transfer_from_dict = {
					'against_voucher_type': 'Project',
					'against_voucher': row2.project,

					'project': row2.project,
					'fund_class': row2.fund_class,
					'service_area': row2.ff_service_area,
					'subservice_area': row2.ff_subservice_area,
					'product': row2.ff_product,     
					'debit': credit_debit,
					'debit_in_account_currency': credit_debit,
					'debit_in_transaction_currency': credit_debit
				}
				transfer_from_dict.update(same_dict)
				# End Transfer From Dict
				
				gl_entries += [transfer_from_dict, transfer_to_dict]
	
	return gl_entries

	# pretty_json = json.dumps(process_entries, indent=4, sort_keys=True)
	# print(pretty_json)
