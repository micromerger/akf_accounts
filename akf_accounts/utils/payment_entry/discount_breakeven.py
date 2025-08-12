import frappe, erpnext
from frappe.utils import (
	getdate
)

# .js api call
@frappe.whitelist()
def create_donor(self):
	def create_party_link(donor_id):
		pargs = {
			'primary_role': 'Supplier', 
			'primary_party': self.party, 
			'secondary_role': 'Donor', 
			'secondary_party': donor_id
		}
		if(not frappe.db.exists('Party Link', pargs)):
			pargs.update({
				'doctype': 'Party Link'
			})
			doc = frappe.get_doc(pargs)
			doc.flags.ignore_permissions = True
			doc.save()

	args = {
		'donor_identity': 'Known',
		'donor_type': 'Individual',
		'donor_name': self.party_name,
		'cnic': '',	
		'email': '',
		'company': self.company,
		'default_currency': 'PKR',
	}
	donor_id = frappe.db.get_value('Donor', args, 'name')
	if(donor_id):
		create_party_link(donor_id)
		self.custom_discount_donor = donor_id
		self.db_set('custom_discount_donor', donor_id)
		# frappe.msgprint('Donor already exist.', indicator='orange', alert=1)
	else:
		args.update({
			'doctype': 'Donor'
		})
		doc = frappe.get_doc(args)
		doc.flags.ignore_mandatory = True		
		doc.flags.ignore_permissions = True
		doc.save()
		self.custom_discount_donor = doc.name
		self.db_set('custom_discount_donor', doc.name)
		create_party_link(doc.name)
		# frappe.msgprint('Donor created successfully!', indicator='green', alert=1)

# .js api call
@frappe.whitelist()
def create_draft_donation(self):

	if(not self.custom_apply_discount_breakeven):
		return

	if((self.custom_discount_amount or 0.0) <= 0.0):
		return

	# Create Donor
	create_donor(self)

	args = {
		'doctype': 'Donation',
		'donor_identity': 'Known',
		'contribution_type': 'Donation',
		'company': self.company,
		'due_date': getdate(),
		'currency': erpnext.get_company_currency(self.company),
		'exchange_rate': 1,
		'donation_cost_center': erpnext.get_default_cost_center(self.company),
		'payment_detail': [{
			'donor_id': self.custom_discount_donor,
			'donation_type': self.custom_intention,
			'fund_class_id': self.custom_donation_fund_class,
			'donation_amount': self.custom_discount_amount,
			'mode_of_payment': self.mode_of_payment,
			'account_paid_to': self.paid_from
		}],
		'reference_doctype': self.doctype,
		'reference_docname': self.name,
	}
	doc = frappe.get_doc(args)
	doc.flags.ignore_mandatory = True
	doc.flags.ignore_permissions = True
	doc.save()
	doc.submit()
	self.db_set('custom_donation', doc.name)
	make_gl_to_adjust_discount_breakeven(self, doc)
	frappe.msgprint('Donation created successfully!', indicator='green', alert=1)

def make_gl_to_adjust_discount_breakeven(self, doc):
	
	args = frappe._dict({
			'doctype': 'GL Entry',
			'posting_date': doc.posting_date,
			'transaction_date': doc.posting_date,
			'against': f"Donation: {doc.name}",
			'against_voucher_type': doc.doctype,
			'against_voucher': doc.name,
			'voucher_type': doc.doctype,
			'voucher_no': doc.name,
			'voucher_subtype': 'Receive',
			'company': doc.company,
			'transaction_currency': doc.currency,
			'transaction_exchange_rate': doc.exchange_rate,
		})
	for row in doc.payment_detail:
		# Receivable creditors entry.
		args.update({
				"party_type": "Donor",
				"party": row.donor_id,
				"account": row.receivable_account,
				"voucher_detail_no": row.name,
				"donor": row.donor_id,

				"fund_class": row.fund_class_id,
				"service_area": row.pay_service_area,
				"subservice_area": row.pay_subservice_area,
				"product": row.pay_product if(row.pay_product) else row.product,
				"donation_type": row.donation_type,
				"donor_desk": row.donor_desk_id,
				"cost_center": row.cost_center,

				"inventory_scenario": row.inventory_scenario,
				
				# "debit": row.base_net_amount,
				"credit": row.base_donation_amount,
				# "debit_in_account_currency": row.net_amount,
				"credit_in_account_currency": row.donation_amount,
				# "debit_in_transaction_currency": row.net_amount,
				"credit_in_transaction_currency": row.donation_amount,
			})
		doc = frappe.get_doc(args)
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_permissions = True
		doc.save()
		doc.submit()

		# Payable debtors entry.
		args.update({		
			"account": self.paid_to,
			"debit": row.base_donation_amount,
			"credit": 0,
			"debit_in_account_currency": row.donation_amount,
			"credit_in_account_currency": 0,
			"debit_in_transaction_currency": row.donation_amount,
			"credit_in_transaction_currency": 0,
		})
		doc = frappe.get_doc(args)
		doc.flags.ignore_mandatory = True
		doc.flags.ignore_permissions = True
		doc.save()
		doc.submit()

