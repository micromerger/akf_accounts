import frappe
import json
from erpnext.stock.doctype.stock_entry.stock_entry import StockEntry
from frappe.model.mapper import get_mapped_doc
from frappe.utils import flt

# Mubarrim, 07-03-2025

from akf_accounts.utils.stock_entry.inventory_to_asset  import create_asset_item_and_asset
from akf_accounts.utils.stock_entry.restricted_inventory import create_restricted_inventory_gl_entries

class XStockEntry(StockEntry):
	def before_validate(self):
		super(XStockEntry, self).before_validate()
		self.set_warehouse_cost_centers()

	def validate(self):
		super(XStockEntry, self).validate()
		self.validate_difference_account()
		self.set_warehouse_cost_centers()
		self.set_total_quantity_count()
		self.set_actual_quantity_before_submission()
		self.stock_between_third_party_warehouse() #Mubarrim

	def validate_difference_account(self):
		if(self.stock_entry_type in ["Inventory to Asset", "Material Receipt"]):
			company = frappe.get_doc("Company", self.company)
			for d in self.get("items"):
				if(self.donation and self.stock_entry_type == "Material Receipt"): 
					d.expense_account = company.custom_default_inventory_fund_account
				elif(self.stock_entry_type == "Inventory to Asset"):
					d.expense_account = get_asset_category_account(d.item_code)

	def set_warehouse_cost_centers(self):
		for row in self.items:
			self.project = row.project
			if (self.purpose == "Material Receipt"):
				row.cost_center = frappe.db.get_value("Warehouse", row.t_warehouse, "custom_cost_center")
			elif (self.purpose == "Material Issue" or self.purpose == "Material Transfer"):
				row.cost_center = frappe.db.get_value("Warehouse", row.s_warehouse, "custom_cost_center")
	
	def set_total_quantity_count(self):
		self.custom_total_quantity_count = sum([item.qty for item in self.get("items")])
			
	def set_actual_quantity_before_submission(self):
			for item in self.items:
				item.custom_actual_quantity = item.actual_qty
	
	def stock_between_third_party_warehouse(self): #Mubarrim
		if(self.purpose == "Material Transfer"):
			for item in self.items:
				if(item.custom_source_warehouse_tpt or item.custom_target_warehouse_tpt):
					frappe.throw("Not allowed for Third Party Warehouse")
						   
	def on_submit(self):
		super(XStockEntry, self).on_submit()
		self.calculate_per_installed_for_delivery_note()
		self.set_material_request_status_per_outgoing_stock_entry()
		self.update_stock_ledger_entry()
		create_restricted_inventory_gl_entries(self)
		create_asset_item_and_asset(self) #Mubarrim
	
	def make_gl_entries(self, gl_entries=None, from_repost=False): #Mubarrim
		for item in self.items:
			if item.custom_source_warehouse_tpt == "For Third Party" or item.custom_target_warehouse_tpt == "For Third Party":
				# frappe.msgprint("GL Entry skipped for this Stock Entry as it contains Third Party Warehouse.")
				return  # Skip GL Entry creation
	
		super().make_gl_entries(gl_entries, from_repost)
	
	def calculate_per_installed_for_delivery_note(self):
		if (not self.custom_delivery_note):
			return
		total_received_qty = 0.0
		total_actual_qty = 0.0
		for row in self.items:
			received_qty = self.get_receive_lost_qty(row)
			if received_qty:
				total_received_qty += received_qty[0][0]
				actual_qty = self.get_actual_qty(row)
				if actual_qty:
					total_actual_qty += actual_qty[0][0]

		return self.set_percent_delivery_note_material_request_status(
			total_received_qty, total_actual_qty
		)

	def get_receive_lost_qty(self, row):
		return frappe.db.sql(
			f""" 
			select ifnull(sum(-1 * actual_qty),0) as qty
			from `tabStock Ledger Entry` 
			where 
				docstatus=1
				and item_code = "{row.item_code}"
				and warehouse = "{row.s_warehouse}" 
				and voucher_no in (select name as qty
					from `tabStock Entry` 
					where docstatus=1 and stock_entry_type = "{self.stock_entry_type}" and custom_delivery_note ="{self.custom_delivery_note}")
		"""
		)

	def get_actual_qty(self, row):
		return frappe.db.sql(
			f"""  
				Select ifnull(sum(actual_qty),0) as actual_qty
				From `tabStock Ledger Entry`
				Where
					docstatus<2
					and item_code = "{row.item_code}"
					and voucher_no = '{self.custom_delivery_note}'
					and warehouse = '{row.s_warehouse}'
			"""
		)

	def set_percent_delivery_note_material_request_status(
		self, total_received_qty, total_actual_qty
	):
		per_installed = (
			(total_received_qty / total_actual_qty) * 100
			if (total_actual_qty > 0)
			else 0.0
		)

		if (self.stock_entry_type == "Material Transfer"):
			frappe.db.sql(
				f""" 
				update `tabDelivery Note`
				set per_installed = {per_installed}, per_billed = {per_installed}
				where name = '{self.custom_delivery_note}'
			"""
			)
		elif (self.stock_entry_type == "Lost / Wastage"):
			frappe.db.set_value(
				"Delivery Note",
				self.custom_delivery_note,
				"custom_lost_wastage",
				per_installed,
			)

		self.update_status_delivery_note_and_material_request()

		return per_installed

	def update_status_delivery_note_and_material_request(self):

		total_percent = frappe.db.sql(
			f""" 
			Select ifnull((per_installed + custom_lost_wastage),0) as total_percent
			From `tabDelivery Note`
			where name = '{self.custom_delivery_note}'
		""",
			as_dict=0,
		)

		if total_percent:
			percent = total_percent[0][0]

			d_status = "To Receive"
			transfer_status = "In Transit"
			m_status = "Partially Received"

			if percent == 100:
				d_status = "Completed"
				transfer_status = "Completed"
				m_status = "Received"

			# Delivery Note
			frappe.db.sql(
				f""" 
					update `tabDelivery Note`
					set status="{d_status}"
					where docstatus =1 
						and name ="{self.custom_delivery_note}"
				"""
			)

			# Material Request
			frappe.db.sql(
				f""" 
					update `tabMaterial Request`
					set transfer_status ="{transfer_status}" ,status="{m_status}", per_ordered =  {percent}
					where name in (select custom_reference_name from `tabDelivery Note` where name="{self.custom_delivery_note}")
				"""
			)

	def set_material_request_status_per_outgoing_stock_entry(self):
		if (not self.outgoing_stock_entry):
			return
		actual_qty = 0.0
		received_qty = 0.0
		for row in self.items:
			_actual_qty = frappe.db.sql(
				f""" Select sum(actual_qty) as qty
						From `tabStock Ledger Entry`
						Where docstatus=1
						and item_code = '{row.item_code}'
						and warehouse = '{row.s_warehouse}' 
						and voucher_no = '{self.outgoing_stock_entry}' """
			)

			if (_actual_qty):
				actual_qty += _actual_qty[0][0]

			_received_qty = frappe.db.sql(
				f""" 
					select ifnull(sum(actual_qty),0) as qty
					from `tabStock Ledger Entry` 
					where 
						docstatus=1
						and item_code = "{row.item_code}"
						and warehouse = "{row.s_warehouse}" 
						and voucher_no in (select name as qty
							from `tabStock Entry` 
							where docstatus=1 and outgoing_stock_entry ="{self.outgoing_stock_entry}")
				"""
			)

			if (_received_qty):
				_received_qty = _received_qty[0][0]
				received_qty += (
					(-1 * _received_qty) if (_received_qty < 0) else _received_qty
				)

		if (actual_qty > 0):
			per_ordered = (received_qty / actual_qty) * 100.0
			status = "Completed" if (per_ordered == 100) else "In Transit"
			frappe.db.sql(
				f""" 
						Update `tabMaterial Request`
						set transfer_status = "{status}",status = "{status}", per_ordered = {per_ordered}
						Where name in (Select material_request 
						From `tabStock Entry Detail` 
						Where docstatus=1 and parent="{self.outgoing_stock_entry}" )"""
			)

	def update_stock_ledger_entry(self):
		source_cost_center, target_cost_center = "", ""
		for row in self.items:
			if frappe.db.exists("Stock Ledger Entry",{ "docstatus": 1,"voucher_no": self.name,}):
				if (self.purpose == "Material Receipt"):
					target_cost_center = frappe.db.get_value("Warehouse", row.t_warehouse, "custom_cost_center")
					frappe.db.sql(
					f""" 
						UPDATE `tabStock Ledger Entry`
						SET 
							custom_new = {row.custom_new}, 
							custom_used = {row.custom_used},
							
							project = "{row.project or ''}",
							fund_class = "{row.fund_class or ''}",
							service_area = "{row.service_area or ''}",
							subservice_area = "{row.subservice_area or ''}",
							product = "{row.product or ''}",
							donor = "{row.donor or ''}",			
							donor_desk = "{row.donor_desk or ''}",
							donor_type = "{row.donor_type or ''}",
							donation_type = "{row.donation_type or ''}",
							cost_center = "{target_cost_center}",
							transaction_type = "{row.transaction_type or ''}",
							inventory_flag = "{row.inventory_flag or ''}",
							asset_category = "{row.asset_category or ''}"

						WHERE 
							docstatus=1 
							and voucher_detail_no = '{row.name}'
							and voucher_no = '{self.name}'
					"""
				)
				elif (self.purpose == "Material Issue"):
					source_cost_center = frappe.db.get_value("Warehouse", row.s_warehouse, "custom_cost_center")
					frappe.db.sql(
					f""" 
						UPDATE `tabStock Ledger Entry`
						SET 
							custom_new = {row.custom_new}, 
							custom_used = {row.custom_used}, 
							
							custom_department= "{self.custom_department or ''}",
							
							project = "{row.project or ''}",
							fund_class = "{row.fund_class or ''}",
							service_area = "{row.service_area or ''}",
							subservice_area = "{row.subservice_area or ''}",
							product = "{row.product or ''}",
							donor = "{row.donor or ''}",			
							donor_desk = "{row.donor_desk or ''}",
							donor_type = "{row.donor_type or ''}",
							donation_type = "{row.donation_type or ''}",
							cost_center = "{source_cost_center}",
							transaction_type = "{row.transaction_type or ''}",
							inventory_flag = "{row.inventory_flag or ''}",
							asset_category = "{row.asset_category or ''}"
							
							
						WHERE 
							docstatus=1 
							and voucher_detail_no = '{row.name}'
							and voucher_no = '{self.name}'
					""")
				elif (self.purpose == "Material Transfer"):
					source_cost_center = frappe.db.get_value("Warehouse", row.s_warehouse, "custom_cost_center")
					frappe.db.sql(
					f""" 
						UPDATE `tabStock Ledger Entry`
						SET 
							custom_new = {row.custom_new}, 
							custom_used = {row.custom_used}, 
							
							custom_department = "{self.custom_department or ''}",
							
							project = "{row.project or ''}",
							fund_class = "{row.fund_class or ''}",
							service_area = "{row.service_area or ''}",
							subservice_area = "{row.subservice_area or ''}",
							product = "{row.product or ''}",
							donor = "{row.donor or ''}",			
							donor_desk = "{row.donor_desk or ''}",
							donor_type = "{row.donor_type or ''}",
							donation_type = "{row.donation_type or ''}",
							cost_center = "{source_cost_center}",
							transaction_type = "{row.transaction_type or ''}",
							inventory_flag = "{row.inventory_flag or ''}",
							asset_category = "{row.asset_category or ''}"
							
						WHERE 
							docstatus=1 
							and voucher_detail_no = '{row.name}'
							and voucher_no = '{self.name}'
							and warehouse= '{row.s_warehouse}'
					""")
					
					target_cost_center = frappe.db.get_value(
						"Warehouse", row.t_warehouse, "custom_cost_center"
					)
					frappe.db.sql(
					f""" 
						UPDATE `tabStock Ledger Entry`
						SET 
							custom_new = {row.custom_new}, 
							custom_used = {row.custom_used}, 
							
							custom_department='{self.custom_department or ''}',
							
							project = "{row.project or ''}",
							fund_class = "{row.fund_class or ''}",
							service_area = "{row.service_area or ''}",
							subservice_area = "{row.subservice_area or ''}",
							product = "{row.product or ''}",
							donor = "{row.donor or ''}",			
							donor_desk = "{row.donor_desk or ''}",
							donor_type = "{row.donor_type or ''}",
							donation_type = "{row.donation_type or ''}",
							cost_center = "{target_cost_center}",
							transaction_type = "{row.transaction_type or ''}",
							inventory_flag = "{row.inventory_flag or ''}",
							asset_category = "{row.asset_category or ''}"
						WHERE 
							docstatus=1 
							and voucher_detail_no = '{row.name}'
							and voucher_no = '{self.name}'
							and warehouse= '{row.t_warehouse}'
					""")
		
		self.update_donor_ids_and_names()
			
	def update_donor_ids_and_names(self):
		if (self.custom_donor_ids):
			# Initialize an empty list to store child values
			donor_ids = []
			donor_names = []
			# Loop through each child record and process the values
			for row in self.custom_donor_ids:
				donor_ids.append(row.donor)
				donor_names.append(row.donor_name)
			
			if frappe.db.exists("Stock Ledger Entry",{"docstatus": 1,"voucher_no": self.name,}):
				donor_ids_as_string = json.dumps(donor_ids)
				frappe.db.sql(
					f""" 
							update 
								`tabStock Ledger Entry`
							set 
								custom_donor_list = '{donor_ids_as_string}'
							where 
								docstatus=1 
								and voucher_no = '{self.name}'
					""")
				donor_names_as_string = json.dumps(donor_names)
				frappe.db.sql(
					f""" 
							update 
								`tabStock Ledger Entry`
							set 
								custom_donor_name_list = '{donor_names_as_string}'
							where 
								docstatus=1 
								and voucher_no = '{self.name}'
					""")

	def on_trash(self):
		self.cancel_linked_records()
		self.reset_delivery_note_percent()

	def on_cancel(self):
		super(XStockEntry, self).on_cancel()
		self.cancel_linked_records()
		self.reset_delivery_note_percent()

	def cancel_linked_records(self):
		if frappe.db.exists("Stock Ledger Entry", {"voucher_no": self.name}):
			frappe.db.sql(
				f""" 
				delete from `tabStock Ledger Entry` where voucher_no = '{self.name}'
			"""
			)
		if frappe.db.exists("GL Entry", {"voucher_no": self.name}):
			frappe.db.sql(
				f""" 
				delete from `tabGL Entry` where voucher_no = '{self.name}'
			"""
			)

	def reset_delivery_note_percent(self):
		if not self.custom_delivery_note:
			return

		per_installed = self.calculate_per_installed_for_delivery_note()
		if self.stock_entry_type == "Lost / Wastage":
			frappe.db.sql(
				f""" 
				update `tabDelivery Note`
				set custom_lost_wastage = custom_lost_wastage - {per_installed}
				where name = '{self.custom_delivery_note}'
			"""
			)
		else:
			frappe.db.sql(
				f""" 
				update `tabDelivery Note`
				set per_installed = per_installed - {per_installed}
				where name = '{self.custom_delivery_note}'
			"""
			)

	

	# or (self.purpose == "Material Transfer" and self.outgoing_stock_entry)
	def validate_qty(self):
		return # Mubashir on 11-08-2025
		super(XStockEntry, self).validate_qty()
		
		def get_conditions(row):
			conditions = f" and item_code='{row.item_code}'"
			conditions += f" and custom_new = '{row.custom_new}' " if (row.custom_new) else " and custom_new = 0 "
			conditions += f" and custom_used = '{row.custom_used}' " if (row.custom_used) else " and custom_used = 0 "
			conditions += f" and warehouse = '{row.s_warehouse}' " if (row.s_warehouse) else " and warehouse IS NULL "
			conditions += f" and custom_cost_center = '{row.cost_center}' " if (row.cost_center) else " and custom_cost_center IS NULL "
			conditions += f" and inventory_flag = '{row.inventory_flag}' " if (row.inventory_flag) else " and inventory_flag = 'Normal' "
			conditions += f" and inventory_scenario = '{row.inventory_scenario}' " if (row.inventory_scenario) else " and inventory_scenario = 'Normal' "
			conditions += f" and service_area = '{row.service_area}' " if (row.service_area) else " and service_area IS NULL "
			conditions += f" and subservice_area = '{row.subservice_area}' " if (row.subservice_area) else " and subservice_area IS NULL "
			conditions += f" and product = '{row.product}' " if (row.product) else " and product IS NULL "
			conditions += f" and project = '{row.project}' "
			# frappe.throw(f"{conditions}")
			return conditions
		
		if ((self.purpose == "Material Issue") or (self.purpose == "Material Transfer")):
			for row in self.items:
				conditions = get_conditions(row)
				query = f"""
						SELECT 
							ifnull(SUM(actual_qty),0) as donated_qty, item_code
						FROM 
							`tabStock Ledger Entry`
						WHERE
							docstatus=1 {conditions}
					"""
				try:
					# frappe.throw(f"Executing query: {query}")
					donated_invetory = frappe.db.sql(
						query,
						as_dict=True,
					)
				except Exception as e:
					frappe.throw(f"Error executing query: {e}")

				for di in donated_invetory:
					# frappe.throw(f"Donated inventory: {di.donated_qty}")
					if di.donated_qty >= row.qty:
						pass
					else:
						frappe.throw(
					f"Insufficient qty for item <b>{row.item_code}</b>, "
					f"requested qty: <b>{row.qty}</b>, available qty: <b>{di.donated_qty}</b>"
					,title="Insufficient Qty")

@frappe.whitelist()
def make_stock_in_lost_entry(source_name, target_doc=None):
	def set_missing_values(source, target):
		target.stock_entry_type = "Lost / Wastage"
		target.set_missing_values()
		target.make_serial_and_batch_bundle_for_transfer()

	def update_item(source_doc, target_doc, source_parent):
		target_doc.t_warehouse = ""

		if source_doc.material_request_item and source_doc.material_request:
			add_to_transit = frappe.db.get_value("Stock Entry", source_name, "add_to_transit")
			if add_to_transit:
				warehouse = frappe.get_value(
					"Material Request Item", source_doc.material_request_item, "warehouse"
				)
				target_doc.t_warehouse = warehouse

		target_doc.s_warehouse = source_doc.t_warehouse
		target_doc.qty = source_doc.qty - source_doc.transferred_qty
		
		
			

	doclist = get_mapped_doc(
		"Stock Entry",
		source_name,
		{
			"Stock Entry": {
				"doctype": "Stock Entry",
				"field_map": {"name": "outgoing_stock_entry"},
				"validation": {"docstatus": ["=", 1]},
			},
			"Stock Entry Detail": {
				"doctype": "Stock Entry Detail",
				"field_map": {
					"name": "ste_detail",
					"parent": "against_stock_entry",
					"serial_no": "serial_no",
					"batch_no": "batch_no",
				},
				"postprocess": update_item,
				"condition": lambda doc: flt(doc.qty) - flt(doc.transferred_qty) > 0.01,
			},
		},
		target_doc,
		set_missing_values,
	)

	return doclist

def get_asset_category_account(item_code):
	if(item_code):
		asset_category = frappe.db.get_value('Item', item_code, 'asset_category')
		if(asset_category):
			asset_category_account = frappe.db.sql(f"""
					Select  fixed_asset_account
					From `tabAsset Category Account`
					Where parent = '{asset_category}'
			""")
			
			if(asset_category_account):
				return asset_category_account[0][0]
			asset_category_link = frappe.utils.get_link_to_form('Asset Category',asset_category)
			frappe.throw(f"Please set <b>{asset_category_link}</b> asset category account", title="Missing Information")
		
		Item_link = frappe.utils.get_link_to_form('Item',item_code)
		frappe.throw(f"Please set <b>{Item_link}</b> asset category.", title="Missing Information")