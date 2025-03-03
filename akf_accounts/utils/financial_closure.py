import frappe
from frappe.utils import get_link_to_form
def confirmation(doc, method=None): # By Nabeel Saleem
	child_table= []
	if(doc.doctype in ["Donation", "Material Request", "Purchase Receipt", "Purchase Invoice", "Payment Entry"]):
		if(hasattr(doc, "payment_detail")): child_table = doc.payment_detail
		elif(hasattr(doc, "program_details")): child_table = doc.program_details
	
	project = None
	for row in child_table:
		if(hasattr(row, "project_id")): 
			project = row.project_id
		elif(hasattr(row, "pd_project")): 
			project = row.pd_project
		exception_message(doc.doctype, project)

def exception_message(doctype, project):
	if(project):
		financial_status = frappe.db.get_value("Project", project, "custom_financial_close")
		form_link = get_link_to_form("Project", project)
		if(financial_status == "Hard"):
			frappe.throw(f"<b>Transaction not allowed</b>. Because project <b>{form_link}</b> is financially <b>{financial_status.lower()}</b>  closed.", title=f"{doctype}")
		elif(doctype!="Payment Entry" and financial_status == "Soft"):
			frappe.throw(f"<b>Transaction not allowed</b>. Because project <b>{form_link}</b> is financially <b>{financial_status.lower()}</b>  closed.", title=f"{doctype}")
	