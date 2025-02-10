import frappe

from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args

def update_payment_detail(row, values, written_off):
	if(written_off):
		frappe.db.set_value("Payment Detail", row.name, "is_written_off", 1)
	else:
		frappe.db.set_value("Payment Detail", row.name, "bad_debt_expense", values.bad_debt_expense)
		frappe.db.set_value("Payment Detail", row.name, "provision_doubtful_debt", values.provision_doubtful_debt)
		frappe.db.set_value("Payment Detail", row.name, "doubtful_debt_amount", values.doubtful_amount)

# Recording of provision of doubtful debt
def record_provision_of_doubtful_det(self, args, values):
	values = frappe._dict(values)
	values["parent"] = self.name
	for row in frappe.db.sql("select * from `tabPayment Detail` where idx=%(serial_no)s and donor_id=%(donor_id)s and parent=%(parent)s", values, as_dict=1):
		args.update({
			"party_type": "Donor",
			"party": row.donor_id,
			"voucher_detail_no": row.name,
			# Accounting Dimensions
			"program": row.pay_service_area,
			"subservice_area": row.subservice_area,
			"product": row.pay_product if(row.pay_product) else row.product,
			"project": row.project,
			"cost_center": row.cost_center,
		})
		# Bad debt expense (Debit Entry)		
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": values.bad_debt_expense,
			"debit": (self.exchange_rate * values.doubtful_amount),
			"debit_in_account_currency": values.doubtful_amount,
			"debit_in_transaction_currency": values.doubtful_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()

		# Provision for doubt debt (Credit Entry)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": values.provision_doubtful_debt,
			"credit": (self.exchange_rate * values.doubtful_amount),
			"credit_in_account_currency": values.doubtful_amount,
			"credit_in_transaction_currency": values.doubtful_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()
		update_payment_detail(row, values, False)
	frappe.msgprint("Doubtful Debt recorded successfully.", alert=1)

# on actual bad debt written off
def bad_debt_written_off(self, args, values):
	values = frappe._dict(values)
	values["parent"] = self.name
	for row in frappe.db.sql("""select * from `tabPayment Detail` 
			where idx=%(serial_no)s and donor_id=%(donor_id)s and parent=%(parent)s""", values, as_dict=1):
		args.update({
			"party_type": "Donor",
			"party": row.donor_id,
			"voucher_detail_no": row.name,
			# Accounting Dimensions
			"program": row.pay_service_area,
			"subservice_area": row.subservice_area,
			"product": row.pay_product if(row.pay_product) else row.product,
			"project": row.project,
			"cost_center": row.cost_center,
		})
		# Bad debt expense (Credit Entry)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": row.receivable_account,
			"credit": (self.exchange_rate * values.doubtful_amount),
			"credit_in_account_currency": values.doubtful_amount,
			"credit_in_transaction_currency": values.doubtful_amount, 
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

		# Provision for doubtful debt (Debit Entry)
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": values.provision_doubtful_debt,
			"debit": (self.exchange_rate * values.doubtful_amount),
			"debit_in_account_currency": values.doubtful_amount,
			"debit_in_transaction_currency": values.doubtful_amount, 
		})
		cdoc = frappe.get_doc(args)
		cdoc.insert(ignore_permissions=True)
		cdoc.submit()
		update_payment_detail(row, values, True)
  
	frappe.msgprint("Written Off recorded successfully.", alert=1)

# on payment entry submission
def adjust_doubtful_debt(self):
    
	def get_doubtful_debt_amount(custom_donation_payment_detail):
		return frappe.db.get_value("Payment Detail", custom_donation_payment_detail, "*", as_dict=1) or 0.0

	for row in self.references:
		if (row.reference_doctype == "Donation") and (row.outstanding_amount >= 0):
			data = get_doubtful_debt_amount(row.custom_donation_payment_detail) if(row.custom_donation_payment_detail) else {}
			if(data):
				doc = frappe.get_doc(row.reference_doctype, row.reference_name)
				args = doc.get_gl_entry_dict()
				# Credit bad debt expense entry.
				args.update({
					"posting_date": self.posting_date,
					"transaction_date": self.posting_date,
					"account": data.bad_debt_expense,
					"party_type": "Donor",
					"party": data.donor_id,
					"voucher_detail_no": data.name,
					# Accounting Dimensions
					"program": data.pay_service_area,
					"subservice_area": data.subservice_area,
					"product": data.pay_product if(data.pay_product) else data.product,
					"project": data.project,
					"cost_center": data.cost_center,
				})
				cargs = get_currency_args()
				args.update(cargs)
				# Final amount after doubtful debt
				total_after_doubtful_debt = (row.total_amount - data.doubtful_debt_amount)
				extra_amount =  (row.allocated_amount - total_after_doubtful_debt)
				if(extra_amount>0):
					args.update({
						"credit": extra_amount,
						"credit_in_account_currency": extra_amount,
						"credit_in_transaction_currency": extra_amount, 
					})
					doc = frappe.get_doc(args)
					doc.insert(ignore_permissions=True)
					doc.submit()


			