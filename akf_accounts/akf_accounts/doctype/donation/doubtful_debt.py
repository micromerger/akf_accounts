import frappe
from akf_accounts.akf_accounts.doctype.donation.donation import (
    get_currency_args
)
from frappe.utils import getdate

# Function 01
# Recording of provision of doubtful debt
def provision_doubtful_debt_func(self, args, values):
	values = frappe._dict(values)
	values["parent"] = self.name
	for row in frappe.db.sql("select * from `tabPayment Detail` where idx=%(serial_no)s and donor=%(donor_id)s and parent=%(parent)s", values, as_dict=1):
		args.update({
			"posting_date": getdate(),
			"transaction_date": getdate(),
			"party_type": "Donor",
			"party": row.donor,
			"voucher_detail_no": row.name,
			# "project": row.project,
			"cost_center": row.cost_center or self.donation_cost_center,
			# Accounting Dimensions
			"fund_class": row.fund_class,
			"service_area": row.pay_service_area,
			"subservice_area": row.pay_subservice_area,
			"product": row.pay_product if(row.pay_product) else row.product,
			"donor": row.donor,		
			"donor_type": row.donor_type,
   			"donor_desk": row.donor_desk,
			"donation_type": row.intention,
			"transaction_type": row.transaction_type
		})
		# Bad debt expense (Debit Entry)		
		cargs = get_currency_args()
		args.update(cargs)
  
		doubtful_amount = values.doubtful_amount
		args.update({
			"account": values.bad_debt_expense,
			"debit": (self.exchange_rate * doubtful_amount),
			"debit_in_account_currency": doubtful_amount,
			"debit_in_transaction_currency": doubtful_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()

		# Provision for doubt debt (Credit Entry)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": values.provision_doubtful_debt,
			"credit": (self.exchange_rate * doubtful_amount),
			"credit_in_account_currency": doubtful_amount,
			"credit_in_transaction_currency": doubtful_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()
		set_payment_detail_doubtful_debt(row.name, values)
	frappe.msgprint("Doubtful Debt recorded successfully.", alert=1)

def set_payment_detail_doubtful_debt(name, values):
	old_doubtful_amount = frappe.db.get_value("Payment Detail", name, "doubtful_debt_amount") or 0
	total_doubtful_amount = (old_doubtful_amount + values.doubtful_amount)
	frappe.db.set_value("Payment Detail", name, {
						"bad_debt_expense": values.bad_debt_expense,
						"provision_doubtful_debt": values.provision_doubtful_debt,
						"doubtful_debt_amount": total_doubtful_amount
    })

# Function 02
# on actual bad debt written off
def bad_debt_written_off(self, args, values):
	values = frappe._dict(values)
	values["parent"] = self.name
	for row in frappe.db.sql("""select * from `tabPayment Detail` 
			where idx=%(serial_no)s and donor=%(donor_id)s and parent=%(parent)s""", values, as_dict=1):
		args.update({
			"posting_date": getdate(),
			"transaction_date": getdate(),
			"party_type": "Donor",
			"party": row.donor,
			"voucher_detail_no": row.name,
			# Accounting Dimensions
			# "project": row.project,
			"cost_center": row.cost_center or self.donation_cost_center,
			"fund_class": row.fund_class,
			"service_area": row.pay_service_area,
			"subservice_area": row.pay_subservice_area,
			"product": row.pay_product if(row.pay_product) else row.product,
			"donor": row.donor,		
			"donor_type": row.donor_type,
			"donor_desk": row.donor_desk,
			"donation_type": row.intention,
			"transaction_type": row.transaction_type
		})
		# Bad debt expense (Credit Entry)
		cargs = get_currency_args()
		args.update(cargs)

		bad_debt_amount = values.bad_debt_amount
		args.update({
			"account": row.receivable_account,
			"credit": (self.exchange_rate * bad_debt_amount),
			"credit_in_account_currency": bad_debt_amount,
			"credit_in_transaction_currency": bad_debt_amount, 
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

		# Provision for doubtful debt (Debit Entry)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": values.provision_doubtful_debt,
			"debit": (self.exchange_rate * bad_debt_amount),
			"debit_in_account_currency": bad_debt_amount,
			"debit_in_transaction_currency": bad_debt_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()
		# print('------------------')
		# print(bad_debt_amount)
		set_payment_detail_bad_debt_amount(row, bad_debt_amount)
	# frappe.throw('stop')
	frappe.msgprint("Written Off recorded successfully.", alert=1)

def set_payment_detail_bad_debt_amount(row, bad_debt_amount):
	name = row.name
	
	old_bad_debt_amount = frappe.db.get_value("Payment Detail", name, "bad_debt_amount") or 0
	total_bad_debt_amount = (old_bad_debt_amount + bad_debt_amount)

	child_outstanding_amount = (row.outstanding_amount - bad_debt_amount) if(row.outstanding_amount >= total_bad_debt_amount) else (row.donation_amount - total_bad_debt_amount)

	frappe.db.set_value("Payment Detail", name, {
		"is_written_off": 1,
     	"bad_debt_amount": total_bad_debt_amount,
		"outstanding_amount": child_outstanding_amount,
    })
	# Update donation
	donation = frappe.db.get_value("Donation", row.parent,  ['outstanding_amount', 'total_donation'], as_dict=1)
	total_outstanding_amount = (donation.outstanding_amount - bad_debt_amount) if(donation.outstanding_amount >= total_bad_debt_amount) else ((donation.total_donation > total_bad_debt_amount))
	frappe.db.set_value("Donation", row.parent, {
		"outstanding_amount": total_outstanding_amount,
    })
	frappe.db.set_value("Payment Detail", row.name, {
		"doubtful_debt_amount": (row.doubtful_debt_amount - bad_debt_amount),
	})

# on payment entry submission
def adjust_doubtful_debt(self):
    
	def get_doubtful_debt_amount(custom_donation_payment_detail):
		return frappe.db.get_value("Payment Detail", custom_donation_payment_detail, "*", as_dict=1) or 0.0

	for row in self.references:
		if (row.reference_doctype == "Donation") and (row.outstanding_amount >= 0):
			data = get_doubtful_debt_amount(row.custom_donation_payment_detail) if(row.custom_donation_payment_detail) else {}
			if(data):
				if(data.bad_debt_expense and data.provision_doubtful_debt):
					doc = frappe.get_doc(row.reference_doctype, row.reference_name)
					args = doc.get_gl_entry_dict()
					# Credit bad debt expense entry.
					args.update({
						"posting_date": self.posting_date,
						"transaction_date": self.posting_date,
						"party_type": "Donor",
						"party": data.donor,
						"voucher_detail_no": data.name,
						'against_voucher_type': self.doctype,
						'against_voucher': self.name,
						# Accounting Dimensions
						# "project": row.project,
						"cost_center": frappe.db.get_value('Donation', data.parent, 'donation_cost_center'),
						"fund_class": data.fund_class,				
						"service_area": data.pay_service_area,
						"subservice_area": data.pay_subservice_area,
						"product": data.pay_product if(data.pay_product) else data.product,
						"donor": data.donor,		
						"donor_type": data.donor_type,
						"donor_desk": data.donor_desk,
						"donation_type": data.intention,
						"transaction_type": data.transaction_type
					})
					# Final amount after doubtful debt
					# total_after_doubtful_debt = (data.outstanding_amount - self.paid_amount)
					# extra_amount =  (row.allocated_amount - total_after_doubtful_debt)
					# frappe.throw(f"{extra_amount}")
					if(data.outstanding_amount == 0):
						reversal_amount = data.doubtful_debt_amount
						# Bad debt
						cargs = get_currency_args()
						args.update(cargs)
						args.update({
							"account": data.bad_debt_expense,
							"credit": reversal_amount,
							"credit_in_account_currency": reversal_amount,
							"credit_in_transaction_currency": reversal_amount, 
						})
						doc = frappe.get_doc(args)
						doc.insert(ignore_permissions=True)
						doc.submit()
						cargs = get_currency_args()
						args.update(cargs)
						# Provision debt
						args.update({
							"account": data.provision_doubtful_debt,
							"debit": reversal_amount,
							"debit_in_account_currency": reversal_amount,
							"debit_in_transaction_currency": reversal_amount, 
						})
						doc = frappe.get_doc(args)
						doc.insert(ignore_permissions=True)
						doc.submit()
