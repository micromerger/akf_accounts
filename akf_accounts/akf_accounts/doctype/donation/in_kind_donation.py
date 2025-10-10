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
		'donation': self.name,
		'items': [{
			't_warehouse': self.warehouse,
			'item_code': row.item_code,
			'qty': row.qty,
			'basic_rate': row.basic_rate,
			'custom_new': row.new,
			'custom_used': row.used,
			# 'custom_target_project': row.project,
			'fund_class': row.fund_class,
			'service_area': row.service_area,
			'subservice_area': row.subservice_area,
			'product': row.product,
			'donor': row.donor,			
			'donor_desk': row.donor_desk,
			'donor_type': row.donor_type,
			# 'intention': row.intention,
			'donation_type': row.intention,
			'cost_center': row.cost_center,
			'transaction_type': row.transaction_type,
			'inventory_flag': row.inventory_flag or "Donated"
			# 'asset_category': row.asset_category
		} for row in self.items]
	})
	doc = frappe.get_doc(args)
	doc.flags.ignore_permissions = True
	# doc.flags.ignore_mandatory = True
	# doc.flags.ignore_validates = True
	doc.insert()
	# doc.submit()

