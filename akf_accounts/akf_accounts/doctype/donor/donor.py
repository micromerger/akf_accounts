# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe, re
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from frappe.model.mapper import get_mapped_doc
from erpnext import get_default_company, get_default_cost_center, get_company_currency
from frappe.utils import getdate, formatdate, get_link_to_form

from akf_accounts.akf_accounts.doctype.proscribed_person.proscribed_person import process_proscribed_person_detail

email_regex = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,7}\b'

class Donor(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def validate(self):
		from frappe.utils import validate_email_address
		if self.email: validate_email_address(self.email.strip(), True)
		# self.sum_up_dial_code_contact_no()
		verify_email(self)
		self.verify_cnic()
		self.validate_duplicate_cnic()
		self.validate_proscribed_person()
		self.validate_unique_unknown_identity()
		self.validate_default_currency()
		self.validate_default_account()
		self.set_is_group()

	def sum_up_dial_code_contact_no(self):
		if (self.country):
			if(self.contact_no):
				dial_code, phone_mask, phone_regix = self.get_country_details()
				if(dial_code and phone_mask):
					phone_mask = '%s%s'%(dial_code, phone_mask)
					mobileSize = len(self.contact_no)
					maskSize = len(phone_mask)
					
					if(mobileSize<maskSize):
						self.contact_no = '{0}{1}'.format(dial_code, self.contact_no)
					
				verify_numbers(self, phone_regix)

	def get_country_details(self):
		return frappe.db.get_value('Country', {'name': self.country}, ["custom_dial_code", "custom_phone_mask", "custom_phone_regex"])
	
	def verify_cnic(self):
		if(self.identification_type=="CNIC"):
			# Define a regex pattern for CNIC: `xxxxx-xxxxxxx-x`
			cnic_pattern = r"^\d{5}-\d{7}-\d{1}$"
			# Check if CNIC matches the pattern
			if(not self.cnic): return
			if not self.match_regex(cnic_pattern, self.cnic):
				frappe.throw('Please enter a valid CNIC in the format xxxxx-xxxxxxx-x.')

	def match_regex(self, pattern, mystr):
		"""Match the given string with the regex pattern."""
		return re.match(pattern, mystr)
	
	def validate_duplicate_cnic(self):
		# Check if CNIC matches the pattern
		if(not self.cnic): return
		def compare_cnic_with_other():
			if(self.parent_donor): return
			data = frappe.db.sql(f"""
				Select name, department, creation 
				From `tabDonor` 
				Where name!='{self.name}' and parent_donor!='{self.name}' and cnic='{self.cnic}' 
				""", as_dict=1)
			if(data):
				frappe.throw(f"""
					A donor with CNIC <b>{self.cnic}</b> exists.
				""", title="Duplicate CNIC")
		
		compare_cnic_with_other()

	def validate_unique_unknown_identity(self):
		"""Ensure only one Donor with donor_identity = 'Unknown' exists."""
		if getattr(self, "donor_identity", None) != "Unknown":
			return
		exists = frappe.db.exists("Donor", {
			"donor_identity": "Unknown",
			"name": ["!=", self.name],
		})
		if exists:
			frappe.throw(
				"Donor with the donor_identity 'Unknown' already exists",
				title="Duplicate Donor Identity"
			)
		
	
	def validate_proscribed_person(self):
		formatted_cnic = str(self.cnic).replace("-", "")
		if((not self.is_new()) and frappe.db.exists("Donor", {"name": self.name, "status": "Blocked"})):
			frappe.throw("You're unable to make any change. Because, you're in proscribed person list.", title="Donor Blocked")
	
	def validate_default_currency(self):
		def throw_msg():
			frappe.throw(f"Donor with currency: <b>{self.default_currency}</b> exists.", title="Registered")
		# check for root currency, there's no child with same currency.    
		if(self.is_group):
			args = {
				"parent_donor": self.name,
				"default_currency": self.default_currency,
				"default_account": self.default_account
			}
			if(frappe.db.exists("Donor", args)): throw_msg()
		# check child currency not belong to root or any other child.
		else:
			# root currency with parent_donor id.
			if(self.parent_donor):
				args = {
					"name": self.parent_donor,
					"default_currency": self.default_currency,
					"default_account": self.default_account
				}
				if(frappe.db.exists("Donor", args)): throw_msg()
				# child currency with parent_donor id.
				args = {
					"name": ["!=", self.name],
					"parent_donor": self.parent_donor,
					"default_currency": self.default_currency,
					"default_account": self.default_account
				}
				if(frappe.db.exists("Donor", args)): throw_msg()
		
	@frappe.whitelist()
	def validate_default_account(self):
		if(not self.company): return
		if(not self.default_currency): return
		result = frappe.db.sql(f""" Select name From `tabAccount`
				Where 
					disabled=0 
					and is_group=0 
					and account_type = "Receivable" 
					and company='{self.company}'
					and account_currency='{self.default_currency}' """)
		self.default_account = result[0][0] if(result) else ""
	
	def set_is_group(self):
		if(not self.parent_donor):
			self.db_set("is_group", 1)
	
	def after_insert(self):
		self.update_status()
		# 21-08-2025 nabeel saleem
		frappe.enqueue(create_address_and_contact, self=self, publish_progress=False)
		

	def update_status(self):
		if(self.identification_type == "CNIC"):
			formatted_cnic = str(self.cnic).replace("-", "")
			if(frappe.db.exists("Proscribed Person", {"cnic": formatted_cnic})):
				self.status = "Blocked"
				process_proscribed_person_detail(self.cnic, status="Blocked")
	
	

	def create_contact(self):
		if(self.contact_no):
			contact = frappe.new_doc("Contact")
			contact.update(
				{
					"first_name": self.donor_name,
					# "last_name": self.last_name,
					# "salutation": self.salutation,
					"gender": self.gender,
					"designation": self.org_representative_designation or self.representative_designation or self.designation,
					"company_name": self.company_name or self.companyorg,
				}
			)

			if self.email:
				contact.append("email_ids", {"email_id": self.email, "is_primary": 1})

			if self.contact_no:
				contact.append("phone_nos", {"phone": self.contact_no, "is_primary_phone": 1})

			if self.mobile_no or self.representative_mobile or self.org_contact: 
				contact.append("phone_nos", {"phone": self.mobile_no or self.representative_mobile or self.org_contact, "is_primary_mobile_no": 1})
			
			contact.append("links", {"link_doctype": self.doctype, "link_name": self.name, "link_title": self.donor_name})
			contact.flags.ignore_permissions = True
			contact.flags.ignore_mandatory = True
			contact.insert()
			# contact.reload()  # load changes by hooks on contact
			
	def create_address(self):
		if(self.address):
			address = frappe.new_doc("Address")
			address.update(
				{
					"address_title": self.donor_name,
					"address_type": 'Billing',
					"address_line1": self.address,
					"city": self.city,
					"state": self.state,
					"country": self.country,
					"email_id": self.email,
					"phone": self.contact_no,
				}
			)

			address.append("links", {"link_doctype": self.doctype, "link_name": self.name, "link_title": self.donor_name})
			address.flags.ignore_permissions = True
			address.flags.ignore_mandatory = True
			address.insert()
			# address.reload()  # load changes by hooks on address

def create_address_and_contact(self, publish_progress=True):
	self.create_contact()
	self.create_address()

@frappe.whitelist()
@frappe.validate_and_sanitize_search_inputs
def get_donor_primary_contact(doctype, txt, searchfield, start, page_len, filters):
	from frappe import qb
	donor = filters.get("donor")

	con = qb.DocType("Contact")
	dlink = qb.DocType("Dynamic Link")

	return (
		qb.from_(con)
		.join(dlink)
		.on(con.name == dlink.parent)
		.select(con.name, con.email_id)
		.where((dlink.link_name == donor) & (con.name.like(f"%{txt}%")))
		.run()
	)

def verify_numbers(self, phone_regix):
	num_list = {
		"contact_no": "Contact No", 
		# "contact_number_whatsapp": "Contact Number (Whatsapp)", 
		# "contact_no_in_case_of_emergency": "Contact No. in Case of Emergency",
		# "mobilewhatsapp_no": "Mobile/WhatsApp No" 
	}
	for key, value in num_list.items():
		number = self.get(key)
		if number:
			if (not match_regex(phone_regix, number)):
				exception_msg('Please enter valid %s.'%value)

def verify_email(self):
	if(not self.email): return
	if not match_regex(email_regex, self.email):
		exception_msg("Please enter valid email.")
	# if frappe.db.exists('Donor',{'name':['!=', self.name],'email':self.email}):
	# 	exception_msg("Email is already registered.")
  
def match_regex(regex ,mystr):
	return re.match(regex, mystr)

def exception_msg(msg):
	frappe.throw(msg)

def alert_msg(msg):
	frappe.msgprint(msg, alert=1)
 
@frappe.whitelist()
def check_all_donors_against_proscribed_persons():
	all_donors = frappe.get_all("Donor", filters={"cnic": ["!=", ""]}, fields=["name", "cnic", "email"])
	
	# Iterate over each donor
	for donor in all_donors:
		formatted_cnic = donor.cnic.replace("-", "")
		
		proscribed_person = frappe.db.get_value("Proscribed Person", {"cnic": formatted_cnic}, "cnic")
		
		if proscribed_person:
			email_template = frappe.db.get_value("Email Template", {"subject": "Urgent Notification: Proscribed Person Identified"}, ["subject", "response"], as_dict=True)
			if email_template:
				message = email_template["response"].replace("{cnic}", formatted_cnic)
				
				if donor.email:
					try:
						frappe.sendmail(
							recipients=["aqsaabbasee@gmail.com"], 
							subject=email_template["subject"],
							message=message,
							now=True 
						)
						
						frappe.msgprint(f"Proscribed person notification email sent for Donor: {donor.name} (CNIC: {formatted_cnic})")
					
					except Exception as e:
						frappe.log_error(f"Failed to send email for Donor: {donor.name}, Error: {str(e)}", "Email Send Failure")

			frappe.throw(f"Proscribed Person with CNIC {formatted_cnic} found for Donor: {donor.name}. Action required!")
	 
@frappe.whitelist()
def donor_html():
	frappe.msgprint("Hello Function!!")
	
	purchase_receipt = frappe.db.sql("""
		SELECT pr.name, pd.service_area
		FROM `tabPurchase Receipt` as pr 
		INNER JOIN `tabProgram Details` as pd
		ON pr.name = pd.parent
	""", as_dict=True)
	
	if not purchase_receipt:
		frappe.msgprint("No purchase receipts found.")
		return

	service_areas = [rec['service_area'] for rec in purchase_receipt]
	frappe.msgprint("Service Area")
	frappe.msgprint(frappe.as_json(service_areas))
	
	if not service_areas:
		frappe.msgprint("No service areas found.")
		return
	
	# Use tuple to match multiple service areas in the SQL query
	format_strings = ','.join(['%s'] * len(service_areas))
	donor_list = frappe.db.sql(f"""
		SELECT party, cost_center, product, SUM(debit) as total_debit 
		FROM `tabGL Entry`
		WHERE program IN ({format_strings})
		AND party_type = 'Donor'
		GROUP BY party, cost_center, product
	""", tuple(service_areas))

	
	total_amount = frappe.db.sql(f"""
		SELECT SUM(debit) as total_debit 
		FROM `tabGL Entry`
		WHERE program IN ({format_strings})
		AND party_type = 'Donor'
	""", tuple(service_areas), as_dict=True)

	heading = "<h5><strong>List of Donors</strong></h5>"
	
	if donor_list:
		table_header = """
			<table class="table table-bordered" style="border: 2px solid black;">
				<thead style="background-color: #242145; color: white; text-align: left;">
					<tr>
						<th class="text-left" style="border: 1px solid black;">Donor ID</th>
						<th class="text-left" style="border: 1px solid black;">Cost Center</th>
						<th class="text-left" style="border: 1px solid black;">Product</th>
						<th class="text-left" style="border: 1px solid black;">Balance</th>
					</tr>
				</thead>
				<tbody>
		"""
		donor_list_rows = ""
		for d in donor_list:
			row = f"""
				<tr style="background-color: #740544; color: white; text-align: left;">
					<td class="text-left" style="border: 1px solid black;">{d[0]}</td>
					<td class="text-left" style="border: 1px solid black;">{d[1]}</td>
					<td class="text-left" style="border: 1px solid black;">{d[2]}</td>
					<td class="text-left" style="border: 1px solid black;">{d[3]}</td>
				</tr>
			"""
			donor_list_rows += row

		complete_table = heading + table_header + donor_list_rows + "</tbody></table><br>"
		
		if total_amount:
			total_amount_value = total_amount[0]['total_debit']
			complete_table += f"""
				<h5 style="text-align: right;"><strong>Total Amount: {total_amount_value}</strong></h5>
			"""
	else:
		complete_table = "<h5><strong>No Donor has given any funds for this project</strong></h5>"
	
	for pr in purchase_receipt:
		frappe.db.set_value("Donor", pr['name'], "donor_list", complete_table)

	frappe.msgprint(complete_table)

@frappe.whitelist()
def make_foriegn_donor(source_name, target_doc=None):
	def validate_donor_accounting(args):
		if(frappe.db.exists("Donor", 
			{"name": source_name, "default_currency": args.default_currency, "default_account": args.default_account})
		   ):
			frappe.throw(f"Donor with currency <b>{args.default_currency}</b> exists.", title="Registered")
			
		args.update({"parent_donor": source_name})
		if(frappe.db.exists("Donor", args)):
			frappe.throw(f"Donor with currency: {args.default_currency} exists.", title="Registered")
		
	def make_donor_doc(
		doctype: str, source_name: str, target_doc=None, args=None, return_against_rejected_qty=False):
	
		def set_missing_values(source, target):
			doc = frappe.get_doc(target)
			doc.is_group = 0
			doc.parent_donor = source.name
			doc.default_currency = args.default_currency
			doc.default_account = args.default_account
		
		doclist = get_mapped_doc(
			doctype,
			source_name,
			{
				doctype: {
					"doctype": doctype,
					"validation": {
						# "is_group": ["=", 0],
					},
				},
				# "Payment Detail": {
				#     "doctype": "Payment Detail",
				#     "field_map": {"*"},
				#     "postprocess": update_payment_detail,
				# },
				# "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
			},
			target_doc,
			set_missing_values,
		)
		return doclist

	args = frappe._dict(frappe.flags.args) # e.g; {"donor": donor_id, "series_no": 1}
	validate_donor_accounting(args)
	return make_donor_doc("Donor", source_name, target_doc, args)

@frappe.whitelist()
def make_donation(source_name, target_doc=None):
	
	def get_random_id():
		import random
		idx = 1
		return int((1000 + idx) + (random.random() * 9000))

	def set_missing_values(source, target):
		doc = frappe.get_doc(target)
		doc.donor_identity = source.donor_identity
		doc.contribution_type = "Donation"
		doc.company = source.company
		doc.donation_cost_center = get_default_cost_center(doc.company)
		doc.currency = source.default_currency
		doc.to_currency = get_company_currency(doc.company)
		
		doc.append("payment_detail", {
			"random_id": get_random_id(),
			"donor_id": source.name,
			"donor": source.name,
		})

	def update_payment_detail(source_doc, target_doc, source_parent):
		# target_doc.donor_id = source_parent.name
		frappe.msgprint(f"{source_doc}")
		pass
	
	doclist = get_mapped_doc(
		"Donor",
		source_name,
		{
			"Donor": {
				"doctype": "Donation",
				"validation": {
					# "is_group": ["=", 0],
				},
			},
			"Payment Detail": {
				"doctype": "Payment Detail",
				"postprocess": update_payment_detail,
			},
			# "Payment Schedule": {"doctype": "Payment Schedule", "postprocess": update_terms},
		},
		target_doc,
		set_missing_values,
	)
	return doclist

@frappe.whitelist()
def del_data():
	try:
		frappe.db.sql("""DELETE FROM `tabGL Entry` WHERE name = 'ACC-GLE-2024-00002'""")
		frappe.msgprint("Record deleted successfully.")
	except Exception as e:
		frappe.msgprint(f"Error: {e}")
		frappe.log_error(frappe.get_traceback(), 'Delete Data Error')
