import frappe

def set_dimensions(doc, method=None):
	if (doc.purpose == "Material Receipt"):
		if(hasattr(doc, 'donation')):
			if(doc.donation):
				for row in doc.items:
					if frappe.db.exists("GL Entry",
							{ "docstatus": 1,"voucher_no": doc.name}
       				):
						frappe.db.sql(f""" 
							UPDATE `tabGL Entry`
							SET 
								project = "{row.project or ''}",
								fund_class = "{row.fund_class or ''}",
								service_area = "{row.service_area or ''}",
								subservice_area = "{row.subservice_area or ''}",
								product = "{row.product or ''}",
								donor = "{row.donor or ''}",			
								donor_desk = "{row.donor_desk or ''}",
								donor_type = "{row.donor_type or ''}",
								donation_type = "{row.donation_type or ''}",
								cost_center = "{get_warehouse_cost_center(row.t_warehouse)}",
								transaction_type = "{row.transaction_type or ''}",
								inventory_flag = "{row.inventory_flag or ''}",
								asset_category = "{row.asset_category or ''}"

							WHERE 
								docstatus=1 
								and voucher_detail_no = '{row.name}'
								and voucher_no = '{doc.name}'
						""")

def get_warehouse_cost_center(warehouse):
	cost_center = frappe.db.get_value("Warehouse", warehouse, "custom_cost_center")
	if(not cost_center):
		frappe.throw(f"Please set cost center in warehouse <b>{warehouse}</b>", title="Missing Information")