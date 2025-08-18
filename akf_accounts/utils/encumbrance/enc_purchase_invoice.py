import frappe

def update_p_i_accounting_dimensions(doc, method=None):
	# frappe.throw(frappe.as_json(doc.custom_program_details))
	if(hasattr(doc, 'custom_program_details')):
		if(doc.docstatus==1 and doc.custom_program_details):
			frappe.enqueue(p_i_accounting_dimensions, doc=doc)

def p_i_accounting_dimensions(doc):
	for row in doc.custom_program_details:
		frappe.db.sql(f'''
				Update `tabGL Entry`
				Set 
					cost_center='{row.pd_cost_center}',	
					fund_class='{row.pd_fund_class}',
					project='{row.pd_project}',
					service_area='{row.pd_service_area}',
					subservice_area='{row.pd_subservice_area}',
					product='{row.pd_product}',
					donor = '{row.pd_donor}',
					donor_desk = '{row.donor_desk}',
					donation_type = '{row.donation_type}'
				Where
					voucher_no='{doc.name}'
				''')
