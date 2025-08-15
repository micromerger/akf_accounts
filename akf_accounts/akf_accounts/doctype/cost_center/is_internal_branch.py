import frappe

def process_internal_branch_struct(self):
	if(self.is_internal_branch):
		create_supplier_and_customer(self)
	else:
		delete_supplier_and_customer(self)
		
def create_supplier_and_customer(self):
	def create_supplier(self):
		args = {
			"supplier_name": self.cost_center_name,
			"supplier_type": "Individual",
			"is_internal_supplier": 1,
			"cost_center": self.name,
			"custom_resident_type": "N/A"
			}
		if(not frappe.db.exists("Supplier", args)):
			args.update({"doctype": "Supplier"})
			doc = frappe.get_doc(args)
			doc.insert(ignore_permissions=True)

	def create_customer(self):
		args = {
			"customer_name": self.cost_center_name,
			"customer_type": "Individual",
			"is_internal_customer": 1,
			"cost_center": self.name
			}
		if(not frappe.db.exists("Customer", args)):
			args.update({"doctype": "Customer"})
			doc = frappe.get_doc(args)
			doc.insert(ignore_permissions=True)
	create_supplier(self)
	create_customer(self)

def delete_supplier_and_customer(self):
	def delete_supplier():
		filters = {
			"cost_center": self.name
		}
		sId = frappe.db.get_value("Supplier", filters, "name")
		if(sId): frappe.db.delete("Supplier", {"name": sId})
	
	def delete_customer():
		filters = {
			"cost_center": self.name
		}
		cId = frappe.db.get_value("Customer", filters, "name")
		if(cId): frappe.db.delete("Customer", {"name": cId})
	
	delete_supplier()
	delete_customer()