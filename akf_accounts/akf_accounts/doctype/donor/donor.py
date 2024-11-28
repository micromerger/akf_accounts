# Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
# For license information, please see license.txt


import frappe, re
from frappe.contacts.address_and_contact import load_address_and_contact
from frappe.model.document import Document
from erpnext.accounts.utils import get_balance_on
from frappe.utils import getdate, formatdate, get_link_to_form

class Donor(Document):
    def onload(self):
        """Load address and contacts in `__onload`"""
        load_address_and_contact(self)

    def validate(self):
        from frappe.utils import validate_email_address
        if self.email:
            validate_email_address(self.email.strip(), True)
        self.verify_proscribed_person()
        self.verify_cnic()
        self.validate_duplicate_cnic()

    def verify_proscribed_person(self):
        if self.cnic:
            formatted_cnic = self.cnic.replace("-", "")
            
            proscribed_person = frappe.db.get_value("Proscribed Persons", {"cnic": formatted_cnic}, "cnic")
            
            if proscribed_person:
                frappe.throw(f"Proscribed Person with CNIC {formatted_cnic} found.")
                # email_template = frappe.db.get_value("Email Template", {"subject": "Urgent Notification: Proscribed Person Identified"}, ["subject", "response"], as_dict=True)
                
                # if email_template:
                #     message = email_template["response"].replace("{cnic}", formatted_cnic)
                    
                #     frappe.sendmail(
                #         recipients=['aqsaabbasee@gmail.com'],
                #         subject=email_template["subject"],
                #         message=message,
                #         now=True  
                #     )
                    
                #     frappe.msgprint("Proscribed person notification email sent successfully.")
                    
                    

    def verify_cnic(self):
        # Define a regex pattern for CNIC: `xxxxx-xxxxxxx-x`
        cnic_pattern = r"^\d{5}-\d{7}-\d{1}$"
        
        # Check if CNIC matches the pattern
        if not self.match_regex(cnic_pattern, self.cnic):
            frappe.throw('Please enter a valid CNIC in the format xxxxx-xxxxxxx-x.')

    def match_regex(self, pattern, mystr):
        """Match the given string with the regex pattern."""
        return re.match(pattern, mystr)
    
    def validate_duplicate_cnic(self):
        preDonor = frappe.db.get_value('Donor', {'cnic': self.cnic}, ['name', 'department', 'creation'], as_dict=1)
        if(preDonor):
            # get_link_to_form # (doctype: str, name: str, label: str | None = None) -> str:
            frappe.throw(f"""A donor with ID: {get_link_to_form('Donor',preDonor.name)}, already exists created by {preDonor.department} on {formatdate(getdate(preDonor.creation))}.""")
        
@frappe.whitelist()
def check_all_donors_against_proscribed_persons():
    all_donors = frappe.get_all("Donor", filters={"cnic": ["!=", ""]}, fields=["name", "cnic", "email"])
    
    # Iterate over each donor
    for donor in all_donors:
        formatted_cnic = donor.cnic.replace("-", "")
        
        proscribed_person = frappe.db.get_value("Proscribed Persons", {"cnic": formatted_cnic}, "cnic")
        
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
def del_data():
    try:
        frappe.db.sql("""DELETE FROM `tabGL Entry` WHERE name = 'ACC-GLE-2024-00002'""")
        frappe.msgprint("Record deleted successfully.")
    except Exception as e:
        frappe.msgprint(f"Error: {e}")
        frappe.log_error(frappe.get_traceback(), 'Delete Data Error')