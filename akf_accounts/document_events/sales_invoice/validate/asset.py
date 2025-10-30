import frappe

def set_asset_dimensions_in_items_table(doc, method=None):
	dimensions = get_accounting_dimensions()
	if(dimensions):
		for item in doc.items:
			
			if(item.asset):
				doc = frappe.get_doc('Asset', item.asset)
				for fieldname in dimensions:
					item.update({
						fieldname: doc.get(fieldname)
					})

def get_accounting_dimensions():
	dimensions = frappe.db.sql(
		"""
			Select 
				replace(lower(name), ' ', '_') as format_name
			From 
				`tabAccounting Dimension`
		"""
	)
	
	return [d[0] for d in dimensions if(d)]