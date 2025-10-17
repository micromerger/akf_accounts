import frappe

def updating_donation(self, cancelled=False):
	for row in self.references:
		if (row.reference_doctype == "Donation") and (row.outstanding_amount >= 0):
			updating_outstanding_amount(self, row, cancelled)
			

def updating_outstanding_amount(self, row, cancelled):
	def set_payment_detail():
		payment_detail_id  = row.custom_donation_payment_detail
		outstanding_amount = 0.0
		if(payment_detail_id):
			data = get_payment_detail(payment_detail_id)
			donation_amount = data.donation_amount
			outstanding = data.outstanding_amount
			paid_amount = self.paid_amount
			
			if(cancelled):
				if(outstanding> donation_amount): 
					outstanding_amount = donation_amount
				else:
					outstanding_amount = outstanding + paid_amount

			else:
				# outstanding_amount = 660,000 - 600,000
				outstanding_amount = outstanding - paid_amount if(outstanding >= paid_amount) else 0
			
			frappe.db.set_value("Payment Detail", payment_detail_id, 
						"outstanding_amount", outstanding_amount)
	
	def set_donation():
		doc = frappe.get_doc(row.reference_doctype, row.reference_name)
		total_payments_outstanding_amount = sum(d.outstanding_amount for d in doc.payment_detail) or 0
		
		frappe.db.set_value("Donation", doc.name, "outstanding_amount", total_payments_outstanding_amount)
		doc.reload()
		
		paid_amount = frappe.db.sql(f'''
			Select 
   				ifnull(sum(allocated_amount),0) as paid_amount
			From 
   				`tabPayment Entry Reference`
			Where
				docstatus=1
				and reference_name = '{doc.name}'
		''')
		set_status(doc, paid_amount, total_payments_outstanding_amount)

	set_payment_detail()
	set_donation()

def set_status(doc, paid_amount, outstanding_amount):	
	status = None
	print('------------------------')
	print(paid_amount)
	
	if(not paid_amount):
		status = "Unpaid"
	if(paid_amount):
		paid_amount = paid_amount[0][0] or 0
		
		if(paid_amount > 0):
			if(outstanding_amount > 0):
				status = "Partly Paid"
			else:
				status = "Paid"
		else:
			status = "Unpaid"
		
	if(frappe.db.exists(doc.doctype, {"docstatus": 1,"name": doc.name, "is_return": 1})):
		status = "Return"

	frappe.db.set_value("Donation", doc.name, {
		"status": status
	})
		
def get_payment_detail(payment_detail_id):
	return frappe.db.get_value("Payment Detail", payment_detail_id, "*", as_dict=1)

