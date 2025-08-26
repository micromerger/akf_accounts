import frappe
from akf_accounts.utils.accounts_defaults import get_company_defaults
from akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args
from akf_stock.utils.end_transit import end_transit_gl_entries

def create_restricted_inventory_gl_entries(self):
	debit_account, credit_account = "", ""
	company = frappe.get_doc("Company", self.company)

	accounts = get_company_defaults(self.company)
	args = get_gl_entry_dict(self)

	if self.stock_entry_type == "Donated Inventory Receive - Restricted":
		pass

	elif self.stock_entry_type == "Inventory Consumption - Restricted":
		for item in self.items:
			if item.custom_source_warehouse_tpt == "For Third Party":
				pass
			else:
				debit_account = company.custom_default_inventory_expense_account
				credit_account = company.default_income_account

				if not debit_account or not credit_account:
					frappe.throw("Required accounts not found in the company")

				# Create the GL entry for the debit account and update
				debit_entry = get_gl_entry_dict(self)
				debit_entry.update(
					{
						"account": debit_account,
						"debit": self.total_outgoing_value,
						"credit": 0,
						"debit_in_account_currency": self.total_outgoing_value,
						"credit_in_account_currency": 0,
					}
				)
				debit_gl = frappe.get_doc(debit_entry)
				debit_gl.flags.ignore_permissions = True
				debit_gl.insert()
				debit_gl.submit()

				credit_entry = get_gl_entry_dict(self)
				credit_entry.update(
					{
						"account": credit_account,
						"debit": 0,
						"credit": self.total_outgoing_value,
						"debit_in_account_currency": 0,
						"credit_in_account_currency": self.total_outgoing_value,
					}
				)
				credit_gl = frappe.get_doc(credit_entry)
				credit_gl.flags.ignore_permissions = True
				credit_gl.insert()
				credit_gl.submit()

	elif self.stock_entry_type == "Inventory Transfer - Restricted":

		source_cost_center, target_cost_center = "", ""
		for item in self.items:
			source_warehouse = item.s_warehouse
			source_cost_center = frappe.db.get_value(
				"Warehouse", source_warehouse, "custom_cost_center"
			)

			target_warehouse = item.t_warehouse
			target_cost_center = frappe.db.get_value(
				"Warehouse", target_warehouse, "custom_cost_center"
			)

		debit_account = company.default_inventory_account
		# credit_account = company.custom_default_inventory_fund_account

		if not debit_account or not credit_account:
			frappe.throw("Required accounts not found in the company")

		for item in self.items:
			# cost_center = item.cost_center
			service_area = item.to_service_area
			subservice_area = item.to_subservice_area
			product = item.to_product
			project = item.custom_target_project
		# Create the GL entry for the debit account and update
		debit_entry = get_gl_entry_dict(self)
		debit_entry.update(
			{
				"account": debit_account,
				"debit": self.total_incoming_value,
				"cost_center": target_cost_center,
				"credit": 0,
				"debit_in_account_currency": self.total_incoming_value,
				"credit_in_account_currency": 0,
				"service_area": service_area,
				"subservice_area": subservice_area,
				"product": product,
				"project": project,

			}
		)
		debit_gl = frappe.get_doc(debit_entry)
		debit_gl.flags.ignore_permissions = True
		debit_gl.insert()
		debit_gl.submit()

		# credit_entry = get_gl_entry_dict(self)
		# credit_entry.update(
		# 	{
		# 		"account": credit_account,
		# 		"debit": 0,
		# 		"cost_center": target_cost_center,
		# 		"credit": self.total_incoming_value,
		# 		"debit_in_account_currency": 0,
		# 		"credit_in_account_currency": self.total_incoming_value,
		# 		"service_area": service_area,
		# 		"subservice_area": subservice_area,
		# 		"product": product,
		# 		"project": project,
		# 	}
		# )
		# credit_gl = frappe.get_doc(credit_entry)
		# credit_gl.flags.ignore_permissions = True
		# credit_gl.insert()
		# credit_gl.submit()

		# debit_account = company.custom_default_inventory_fund_account
		credit_account = company.default_inventory_account

		if not debit_account or not credit_account:
			frappe.throw("Required accounts not found in the company")
		# Create the GL entry for the debit account and update
		# debit_entry = get_gl_entry_dict(self)
		# debit_entry.update(
		# 	{
		# 		"account": debit_account,
		# 		"debit": self.total_incoming_value,
		# 		"cost_center": source_cost_center,
		# 		"credit": 0,
		# 		"debit_in_account_currency": self.total_incoming_value,
		# 		"credit_in_account_currency": 0,
		# 	}
		# )
		# debit_gl = frappe.get_doc(debit_entry)
		# debit_gl.flags.ignore_permissions = True
		# debit_gl.insert()
		# debit_gl.submit()

		credit_entry = get_gl_entry_dict(self)
		credit_entry.update(
			{
				"account": credit_account,
				"debit": 0,
				"cost_center": source_cost_center,
				"credit": self.total_incoming_value,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": self.total_incoming_value,
			}
		)
		credit_gl = frappe.get_doc(credit_entry)
		credit_gl.flags.ignore_permissions = True
		credit_gl.insert()
		credit_gl.submit()

	elif self.stock_entry_type == "Donated Inventory Disposal - Restricted":
		pass

	elif (self.purpose == "Material Transfer" and self.add_to_transit):
		add_to_transit_gl_entries(self, accounts)

	elif (self.purpose == "Material Transfer" and self.outgoing_stock_entry):
		end_transit_gl_entries(self, args, accounts)
		# debit_account = company.default_inventory_account
		# credit_account = company.custom_default_inventory_fund_account

		# source_cost_center, target_cost_center = "", ""
		# for item in self.items:
		# 	source_warehouse = item.s_warehouse
		# 	source_cost_center = frappe.db.get_value(
		# 		"Warehouse", source_warehouse, "custom_cost_center"
		# 	)

		# 	target_warehouse = item.t_warehouse
		# 	target_cost_center = frappe.db.get_value(
		# 		"Warehouse", target_warehouse, "custom_cost_center"
		# 	)

		# if not debit_account or not credit_account:
		# 	frappe.throw("Required accounts not found in the company")
		# # Create the GL entry for the debit account and update
		# debit_entry = get_gl_entry_dict(self)
		# debit_entry.update(
		# 	{
		# 		"account": debit_account,
		# 		"debit": self.total_incoming_value,
		# 		"cost_center": source_cost_center,
		# 		"credit": 0,
		# 		"debit_in_account_currency": self.total_incoming_value,
		# 		"credit_in_account_currency": 0,
		# 	}
		# )
		# debit_gl = frappe.get_doc(debit_entry)
		# debit_gl.flags.ignore_permissions = True
		# debit_gl.insert()
		# debit_gl.submit()

		# credit_entry = get_gl_entry_dict(self)
		# credit_entry.update(
		# 	{
		# 		"account": credit_account,
		# 		"debit": 0,
		# 		"cost_center": target_cost_center,
		# 		"credit": self.total_incoming_value,
		# 		"debit_in_account_currency": 0,
		# 		"credit_in_account_currency": self.total_incoming_value,
		# 	}
		# )
		# credit_gl = frappe.get_doc(credit_entry)
		# credit_gl.flags.ignore_permissions = True
		# credit_gl.insert()
		# credit_gl.submit()

def get_gl_entry_dict(self):
	cost_center = ""
	service_area = ""
	subservice_area = ""
	product = ""
	project = ""

	for item in self.items:
		cost_center = item.cost_center
		service_area = item.service_area
		subservice_area = item.subservice_area
		product = item.product
		project = item.project

	return frappe._dict(
		{
			"doctype": "GL Entry",
			"posting_date": self.posting_date,
			# "transaction_date": self.posting_date,
			"party_type": "Donor",
			"party": self.donor,
			"against": f"Stock Entry: {self.name}",
			"against_voucher_type": "Stock Entry",
			"against_voucher": self.name,
			"voucher_type": "Stock Entry",
			"voucher_subtype": self.stock_entry_type,
			"voucher_no": self.name,
			"company": self.company,
			"cost_center": cost_center,
			"service_area": service_area,
			"subservice_area": subservice_area,
			"product": product,
			"project": project,
		}
	)


def add_to_transit_gl_entries(self, accounts):
	
	def stock_in_transit(args, source_cost_center):
		# Create the GL entry for the debit account and update
		cargs = get_currency_args()
		args.update(cargs)
		args.update(
			{
				"account": accounts.default_stock_in_transit,
				"debit": self.total_incoming_value,
				"cost_center": source_cost_center,
				"credit": 0,
				"debit_in_account_currency": self.total_incoming_value,
				"credit_in_account_currency": 0,
			}
		)
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def designated_inventory_in_transit_fund(args, target_cost_center):
		cargs = get_currency_args()
		args.update(cargs)
		args.update(
			{
				"account": accounts.designated_inventory_in_transit_fund,
				"debit": 0,
				"cost_center": target_cost_center,
				"credit": self.total_incoming_value,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": self.total_incoming_value,
			}
		)
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def default_inventory_fund_account(args, source_cost_center):
		# Create the GL entry for the debit account and update
		cargs = get_currency_args()
		args.update(cargs)
		args.update(
			{
				"account": accounts.default_inventory_fund_account,
				"debit": self.total_incoming_value,
				"cost_center": source_cost_center,
				"credit": 0,
				"debit_in_account_currency": self.total_incoming_value,
				"credit_in_account_currency": 0,
			}
		)
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()

	def default_inventory_asset_account(args, target_cost_center):
		cargs = get_currency_args()
		args.update(cargs)
		args.update(
			{
				"account": accounts.default_inventory_asset_account,
				"debit": 0,
				"cost_center": target_cost_center,
				"credit": self.total_incoming_value,
				"debit_in_account_currency": 0,
				"credit_in_account_currency": self.total_incoming_value,
			}
		)
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions = True)
		doc.submit()
	
	def default_income_account(args):
		pass

	def start_process():
		args = get_gl_entry_dict(self)
		for row in self.items:
			source_cost_center = frappe.db.get_value("Warehouse", row.s_warehouse, "custom_cost_center")
			target_cost_center = frappe.db.get_value("Warehouse", row.t_warehouse, "custom_cost_center")
			args.update({
				"service_area": row.service_area,
				"subservice_area": row.subservice_area,
				"product": row.product,
				"project": row.project,
			})
			stock_in_transit(args, source_cost_center)
			designated_inventory_in_transit_fund(args, target_cost_center)
			default_inventory_fund_account(args, source_cost_center)
			default_inventory_asset_account(args, target_cost_center)

	start_process()

