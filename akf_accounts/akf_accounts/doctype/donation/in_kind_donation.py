import frappe

# nabeel saleem, 22-08-2025
def make_stock_entry_for_in_kind_donation(self):
	args = frappe._dict({
		'doctype': 'Stock Entry',
		'stock_entry_type': self.stock_entry_type or "Material Receipt",
		'company': self.company,
		'posting_date': self.posting_date,
		'posting_time': self.posting_time,
		'to_warehouse': self.warehouse,
		# 'custom_donor_ids': self.donor_list,
		'donation': self.name,
		'items': [{
			't_warehouse': self.warehouse,
			'item_code': row.item_code,
			'qty': row.qty,
			'basic_rate': row.basic_rate,
			'custom_new': row.new,
			'custom_used': row.used,
			# 'custom_target_project': row.project,
			'custom_fund_class_id': row.fund_class,
			'custom_service_area_id': row.service_area,
			'custom_subservice_area_id': row.subservice_area,
			'custom_product_id': row.product,
			'custom_donor_id': row.donor,			
			'custom_donor_desk_id': row.donor_desk,
			'custom_donor_type_id': row.donor_type,
			'custom_intention_id': row.intention,
			'custom_cost_center_id': row.cost_center,
			'custom_transaction_type_id': row.transaction_type,
			'inventory_flag': row.inventory_flag
			# 'custom_asset_category_id': row.asset_category
		} for row in self.items]
	})
	doc = frappe.get_doc(args)
	doc.flags.ignore_permissions = True
	# doc.flags.ignore_mandatory = True
	# doc.flags.ignore_validates = True
	doc.insert()
	# doc.submit()

