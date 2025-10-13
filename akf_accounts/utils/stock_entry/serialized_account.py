
import frappe

def get_serialized_receipt_difference_account(doc, method=None):
	if(doc.stock_entry_type in ['Material Transfer', 'Material Issue', 'Inventory to Asset']):
		for row in doc.items:
			if(hasattr(row, 'custom_serialized_difference_account')):
				custom_serialized_difference_account = frappe.db.sql(f'''
							Select sd.expense_account
							From `tabStock Entry` se inner join `tabStock Entry Detail` sd on (se.name=sd.parent)
							Where se.docstatus=1
								and se.stock_entry_type = "Material Receipt"
								and sd.item_code = '{row.item_code}'
							  
							Group by 
								sd.expense_account

							Order by 
								se.creation desc

							Limit 1
							  ''')[0][0] or None
				
				if(custom_serialized_difference_account):
					row.custom_serialized_difference_account = custom_serialized_difference_account