# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe, re
from frappe.model.document import Document


class ProscribedPerson(Document):
	def validate(self):
		self.validate_cnic()
		active_or_block_donor(self.cnic)
		set_gl_entry_user_tags(self.cnic)
		set_stock_ledger_user_tags(self.cnic)

	def validate_cnic(self):
		if(not self.cnic): return
		# Define a regex pattern for CNIC: `xxxxx-xxxxxxx-x`
		cnic_pattern = r"^\d{5}-\d{7}-\d{1}$"
		# Check if CNIC matches the pattern
		if (not re.match(cnic_pattern, self.cnic)):
			frappe.throw('CNIC is not valid.', title="Error")

	def on_trash(self):
		active_or_block_donor(self.cnic, status="Active")
		set_gl_entry_user_tags(self.cnic, status="Active")
		set_stock_ledger_user_tags(self.cnic, status="Active")

def active_or_block_donor(cnic, status="Blocked"):
	donorId = frappe.db.get_value("Donor", {"cnic": cnic}, "name")
	if(donorId):
		frappe.db.set_value("Donor", donorId, "status", status)

def set_gl_entry_user_tags(cnic, status="Blocked"):
	donorId = frappe.db.get_value("Donor", {"cnic": cnic}, "name")
	filters = {"is_cancelled": 0, "donor": donorId}
	if(frappe.db.exists("GL Entry", filters)):
		_user_tags = "Proscribed Person" if(status=="Blocked") else "-"
		frappe.db.set_value("GL Entry", filters, "_user_tags", _user_tags)

def set_stock_ledger_user_tags(cnic, status="Blocked"):
	donorId = frappe.db.get_value("Donor", {"cnic": cnic}, "name")
	filters = {"docstatus": 1, "donor": donorId}
	if(frappe.db.exists("Stock Ledger Entry", filters)):
		_user_tags = "Proscribed Person" if(status=="Blocked") else "-"
		frappe.db.set_value("Stock Ledger Entry", filters, "_user_tags", _user_tags)