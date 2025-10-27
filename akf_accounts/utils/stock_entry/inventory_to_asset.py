import frappe
def create_asset_item_and_asset(self):
	if (self.stock_entry_type != "Inventory to Asset"):
		return
	'''def create_asset_category(row):
		if(frappe.db.exists("Asset Category", {"asset_category_name": row.item_group})):
			return row.item_group
		else:
			doc = frappe.get_doc({
				"doctype": "Asset Category",
				"asset_category_name": row.item_group,
				"accounts": 
					[{
						"company_name": self.company,
						"fixed_asset_account": "Capital Equipments - AKFP",
					}]
				})
			doc.insert(ignore_permissions=True)
			return doc.name'''

	def create_asset_item(row):
		if (frappe.db.exists("Item", {"item_name":f"Asset-{row.item_name}"})):
			return frappe.db.get_value("Item", {"item_name":f"Asset-{row.item_name}"}, "name")
		else:
			doc = frappe.get_doc({
				"doctype": "Item",
				"item_code": f"Asset-{row.item_name}",
				"item_name": f"Asset-{row.item_name}",
				"item_group": row.item_group, 
				"stock_uom": row.uom,
				"is_stock_item": 0,
				"is_fixed_asset": 1,
				"asset_category": frappe.db.get_value('Item', row.item_code, 'asset_category'),
				"custom_source_of_asset_acquistion": f'{row.inventory_flag}',
				"custom_type_of_asset": f'{row.transaction_type}'
			})
			doc.insert(ignore_permissions=True)
			
			return doc.name
	def create_asset(row, item_code):
		doc = frappe.get_doc({
			"doctype": "Asset",
			"item_code": item_code,
			"company": self.company,
			"location": row.custom_asset_location,
			# "custom_source_of_asset_acquistion": f'{row.inventory_flag}',
			# "custom_type_of_asset": f'{row.custom_transaction_type}',
			"available_for_use_date": frappe.utils.nowdate(),
			"gross_purchase_amount": row.basic_rate,
			"asset_quantity": 1,
			"is_existing_asset": 1,
			"custom_against_stock_entry": self.name,

			# "cost_center": row.cost_center,
			# "service_area": row.service_area,
			# "subservice_area": row.subservice_area,
			# "product": row.product,
			# "project": row.project,
			# "donor": row.donor,
			# "task": row.task,
			# "inventory_flag": row.inventory_flag,
			# "inventory_scenario":row.inventory_scenario
			#Updated Dimensions, Mubarrim - August 26, 2023
			"project" : row.project,
			"fund_class" : row.fund_class,
			"service_area" : row.service_area,
			"subservice_area" : row.subservice_area,
			"product" : row.product,
			"donor" : row.donor,			
			"donor_desk" : row.donor_desk,
			"donor_type" : row.donor_type,
			"donation_type" : row.donation_type,
			"cost_center" : row.cost_center,
			"transaction_type" : row.transaction_type,
			"inventory_flag" : row.inventory_flag,
			"asset_category" : row.asset_category
		})
		doc.insert(ignore_permissions=True)
	assets_list = []
	for row in self.items:
		# asset_category = create_asset_category(row)
		item_code = create_asset_item(row)
		for asset_qty in range(int(row.qty)):  
			create_asset(row, item_code)
		assets_list.append(item_code)
	if (assets_list):
		frappe.msgprint(f"Assets are created for items: {', '.join(assets_list)}", alert=1)
	else:
		frappe.throw("No new assets created.", title=f"{self.stock_entry_type}")
