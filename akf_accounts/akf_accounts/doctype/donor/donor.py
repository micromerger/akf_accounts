# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe, re
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on



class Donor(Document):
	def onload(self):
		"""Load address and contacts in `__onload`"""
		load_address_and_contact(self)

	def validate(self):
		from frappe.utils import validate_email_address
		if self.email:
			validate_email_address(self.email.strip(), True)
		# frappe.msgprint("Balance from Donor!")
		# party_balance = get_balance_on(party_type="Donor", party="DONOR-2024-00012", cost_center="Rawalpindi Branch - AKFP")
		# frappe.msgprint(frappe.as_json(party_balance))
        

	def verify_cnic(self):
		if (not match_regex("", self.custom_cnic)):
			exception_msg('Please enter valid %s.'%details.custom_label)
		
	def match_regex(regex ,mystr):
		return re.match(regex, mystr)
              
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
def del_data():
    try:
        frappe.db.sql("""DELETE FROM `tabGL Entry` WHERE name = 'ACC-GLE-2024-00002'""")
        frappe.msgprint("Record deleted successfully.")
    except Exception as e:
        frappe.msgprint(f"Error: {e}")
        frappe.log_error(frappe.get_traceback(), 'Delete Data Error')