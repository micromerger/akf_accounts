import frappe

def create_pledge_donation(doc, method=None):
	self = doc
	if (not self.fund_class_id):
		frappe.throw("Fund Class ID is required to create a donation entry.")
	if (not self.branch):
		frappe.throw("Branch is required to create a donation entry.")
	if (not self.intention):
		frappe.throw("Intention is required to create a donation entry.")
	if (not self.sponsorship_tenure):
		frappe.throw("Sponsorship Tenure is required to create a donation entry.")
	if (not self.tenure_period):
		frappe.throw("Tenure Period is required to create a donation entry.")        
	if (not self.sponsored_amount):
		frappe.throw("Sponsored Amount is required to create a donation entry.")
	
	cdoc = frappe.new_doc("Donation")
	cdoc.donor_identity = 'Known'
	cdoc.contribution_type = 'Pledge'
	cdoc.currency = 'PKR'
	cdoc.company = self.company
	cdoc.donation_cost_center = self.branch
	
	cdoc.append("payment_detail", {
	"fund_class": self.fund_class_id,
	"intention": self.intention,
	"transaction_type": self.custom_transaction_type,
	"donor": self.donor_id,
	"donation_amount": self.sponsored_amount,
	"due_date": self.end_date
	})

	cdoc.insert(ignore_permissions=True)
	self.donation = cdoc.name
	self.reload()

