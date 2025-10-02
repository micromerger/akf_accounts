# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe.model.document import Document


class PaymentDetail(Document):
	def before_submit(self):
		# For return documents, ensure receipt_number is unique
		if self.parent and frappe.db.get_value("Donation", self.parent, "is_return"):
			if self.receipt_number:
				# Check if receipt_number already exists for non-return documents
				existing = frappe.db.sql("""
					SELECT pd.name 
					FROM `tabPayment Detail` pd 
					INNER JOIN `tabDonation` d ON pd.parent = d.name 
					WHERE pd.receipt_number = %s 
					AND d.is_return = 0 
					AND pd.name != %s
				""", (self.receipt_number, self.name))
				
				if existing:
					frappe.throw(f"Receipt Number '{self.receipt_number}' already exists for another donation.")
