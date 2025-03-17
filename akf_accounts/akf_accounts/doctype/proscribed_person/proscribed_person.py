# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe, re
from frappe.model.document import Document


class ProscribedPerson(Document):
	def validate(self):
		self.validate_cnic()

	def validate_cnic(self):
		if(not self.cnic): return
		# Define a regex pattern for CNIC: `xxxxx-xxxxxxx-x`
		cnic_pattern = r"^\d{5}\d{7}\d{1}$"
		# Check if CNIC matches the pattern
		if (not re.match(cnic_pattern, self.cnic)):
			frappe.throw('CNIC is not valid.', title="Error")

	def after_insert(self):
		process_proscribed_person_detail(self.cnic)
		self.reload()

	def on_trash(self):
		process_proscribed_person_detail(self.cnic, status="Active")

# 1
def active_or_block_donor(donor_id, status="Blocked"):
	# frappe.throw(f"{donor_id} {status}")
	if(donor_id): frappe.db.set_value("Donor", donor_id, "status", status)
# 2
def set_donor_in_proscribed_person(cnic):
	# cnic = str(cnic).replace("-", "")
	# name = frappe.db.get_value("Proscribed Person", {"cnic": cnic}, "name")
	if(name):
		pass
		# donor_id = get_donor(cnic)
		# donor_name = frappe.db.get_value("Donor", donor_id, "donor_name")
		# frappe.db.set_value("Proscribed Person", name, "donor", donor_id)
		# frappe.db.set_value("Proscribed Person", name, "donor_name", donor_name)
# 3
def add_user_tags_gl_entry(donor_id, status="Blocked"):
	if(donor_id):
		filters = {"is_cancelled": 0, "donor": donor_id}
		if(frappe.db.exists("GL Entry", filters)):
			_user_tags = "Proscribed Person" if(status=="Blocked") else ""
			frappe.db.set_value("GL Entry", filters, "_user_tags", _user_tags)
			# frappe.db.sql(f"""Update `tabGL Entry` Set _user_tags='{_user_tags}' Where is_cancelled=0 and donor='{donor_id}' """)
# 4
def add_user_tags_stock_ledger_entry(donor_id, status="Blocked"):
	if(donor_id):
		sle_voucher_nos = frappe.db.sql(f""" select donor, parent  from `tabDonor List` where donor = "{donor_id}" """, as_dict=1)
		for d in sle_voucher_nos:
			filters = {"docstatus": 1, "voucher_no": d.parent}
			if(frappe.db.exists("Stock Ledger Entry", filters)):
				_user_tags = "Proscribed Person" if(status=="Blocked") else ""
				frappe.db.set_value("Stock Ledger Entry", filters, "_user_tags", _user_tags)

def format_cnic(cnic):
	if(len(cnic) == 15): return cnic
	# Convert the CNIC number to a string if it's not already
	cnic_str = str(cnic)
	# Ensure the CNIC has exactly 13 digits
	if (len(cnic_str) != 13 or not cnic_str.isdigit()):
		raise ValueError("CNIC must be a 13-digit number")    
	# Format the CNIC using slicing
	formatted_cnic = f"{cnic_str[:5]}-{cnic_str[5:12]}-{cnic_str[12]}"
	return formatted_cnic

def get_donor(cnic):
	cnic = format_cnic(cnic)
	return frappe.db.get_list("Donor", filters={"cnic": cnic}, fields=["name"])
		
# Process to block the donor...
def process_proscribed_person_detail(cnic, status="Blocked"):
	donor_ids = get_donor(cnic)
	for Id in donor_ids:
		active_or_block_donor(Id, status=status)
		set_donor_in_proscribed_person(cnic)
		add_user_tags_gl_entry(Id, status=status)
		add_user_tags_stock_ledger_entry(Id, status=status)
	