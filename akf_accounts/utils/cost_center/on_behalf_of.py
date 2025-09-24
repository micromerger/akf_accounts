import frappe

def process_internal_branch_struct(doc, method=None):
	self = doc
	if(self.custom_on_behalf_of):
		create_supplier_and_customer(self)
	else:
		delete_supplier_and_customer(self)
		
def create_supplier_and_customer(self):
    
	def create_supplier(self):
		if(not frappe.db.exists("Supplier", {"cost_center": self.name})):
			args = {
				"supplier_name": self.cost_center_name,
				"supplier_type": "Individual",
				"custom_resident_type": "N/A",
				"custom_on_behalf_of": 1,
				"cost_center": self.name,
				"doctype": "Supplier"
			}
			doc = frappe.get_doc(args)
			doc.flags.ignore_mandatory = True
			doc.flags.ignore_permissions = True
			doc.insert()
			return True	
		return False
		
	def create_customer(self):
		if(not frappe.db.exists("Customer", {"cost_center": self.name})):
			args = {
				"customer_name": self.cost_center_name,
				"customer_type": "Individual",
				"custom_on_behalf_of": 1,
				"cost_center": self.name,
				"doctype": "Customer"
   			}
			doc = frappe.get_doc(args)
			doc.flags.ignore_mandatory = True
			doc.flags.ignore_permissions = True
			doc.insert()
			return True
		return False	

	Is_Created = create_supplier(self)
	Is_Created = create_customer(self)
	if(Is_Created):
		success_message("Internal <b>(Supplier & Customer)</b> are created successfully.")


def delete_supplier_and_customer(self):
    
	def delete_supplier():
		filters = {
			"cost_center": self.name
		}
		sId = frappe.db.get_value("Supplier", filters, "name")
		if(sId): 
			frappe.db.delete("Supplier", {"name": sId})
			return True
		else:
			return False
	
	def delete_customer():
		filters = {
			"cost_center": self.name
		}
		cId = frappe.db.get_value("Customer", filters, "name")
		if(cId): 
			frappe.db.delete("Customer", {"name": cId})
			return True
		else:
			return False
	
	Is_Deleted = delete_supplier()
	Is_Deleted = delete_customer()
	if(Is_Deleted): 
		success_message("Internal <b>(Supplier & Customer)</b> are deleted successfully.")

def success_message(msg):
	frappe.msgprint(msg, alert=True)