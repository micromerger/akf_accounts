import frappe

def update_stock_dimensions(doc, method=None):
	self = doc

	for dimensions in self.custom_program_details:
		fields_list = []
		if(dimensions.pd_project): fields_list += [f" project = '{dimensions.pd_project}' "]
		if(dimensions.pd_cost_center): fields_list += [f" cost_center = '{dimensions.pd_cost_center}' "]
		if(dimensions.pd_fund_class): fields_list += [f" fund_class = '{dimensions.pd_fund_class}' "]
		if(dimensions.pd_service_area): fields_list += [f" service_area = '{dimensions.pd_service_area}' "]
		if(dimensions.pd_subservice_area): fields_list += [f" subservice_area = '{dimensions.pd_subservice_area}' "]
		if(dimensions.pd_product): fields_list += [f" product = '{dimensions.pd_product}' "]
		if(dimensions.pd_donor): fields_list += [f" donor = '{dimensions.pd_donor}' "]
		if(dimensions.pd_donor_type): fields_list += [f" donor_type = '{dimensions.pd_donor_type}' "]
		if(dimensions.pd_donor_desk): fields_list += [f" donor_desk = '{dimensions.pd_donor_desk}' "]
		if(dimensions.pd_intention): fields_list += [f" donation_type = '{dimensions.pd_intention}' "]
		if(dimensions.pd_transaction_type): fields_list += [f" transaction_type = '{dimensions.pd_transaction_type}' "]
		set_query_string = ",".join(fields_list)
		
		for row in self.items:
			if frappe.db.exists(
				"Stock Ledger Entry",
				{
					"docstatus": 1,
					"voucher_no": self.name,
				},
			):
				frappe.db.sql(
					f""" 
					UPDATE `tabStock Ledger Entry`
					SET 
						{set_query_string},
						custom_new = {row.custom_new},
						custom_used = {row.custom_used}
					WHERE
						docstatus = 1 
						AND voucher_detail_no = '{row.name}'
						AND voucher_no = '{self.name}'
					"""
				)