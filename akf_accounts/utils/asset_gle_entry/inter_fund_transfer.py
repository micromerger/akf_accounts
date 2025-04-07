import frappe
from frappe.utils import getdate
from akf_accounts.utils.accounts_defaults import get_company_defaults
from erpnext.accounts.utils import get_company_default
from  akf_accounts.akf_accounts.doctype.donation.donation import get_currency_args

def make_asset_inter_fund_transfer_gl_entries(self):
	if (self.purpose != "Inter Fund Transfer"): 
		return
	if(not get_company_default(self.company, "custom_enable_asset_accounting", ignore_validation=True)): 
		return
	
	# credit and debit both
	def default_asset_account(args, row):
		total_asset_cost = row.total_asset_cost
		args.update({
			"account": self.default_asset_account,
			"cost_center": row.source_cost_center,
			"donor": row.donor,
			"task": row.task,
			"inventory_flag": row.inventory_flag,
			"inventory_scenario":row.inventory_scenario
		})
		# credit with current dimensions changes
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"credit": total_asset_cost,
			"credit_in_account_currency": total_asset_cost,
			"credit_in_transaction_currency": total_asset_cost,
			"service_area": row.service_area,
			"subservice_area": row.subservice_area,
			"product": row.product,
			"project": row.project,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()

		args.update({
			"debit": total_asset_cost,
			"debit_in_account_currency": total_asset_cost,
			"debit_in_transaction_currency": total_asset_cost,
			"service_area": row.target_service_area if(row.target_service_area) else row.service_area,
			"subservice_area": row.target_subservice_area if(row.target_subservice_area) else row.subservice_area,
			"product": row.target_product if(row.target_product) else row.product,
			"project": row.target_project,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	# credit and debit both
	def default_designated_asset_fund_account(args, row):
		cargs = get_currency_args()
		args.update(cargs)
		args.update({
			"account": self.default_designated_asset_fund_account,
			"cost_center": row.source_cost_center,
			"donor": row.donor,
			"task": row.task,
			"inventory_flag": row.inventory_flag,
			"inventory_scenario":row.inventory_scenario
		})
		total_asset_cost = row.total_asset_cost
		args.update({
			"debit": total_asset_cost,
			"debit_in_account_currency": total_asset_cost,
			"debit_in_transaction_currency": total_asset_cost,
			"service_area": row.service_area,
			"subservice_area": row.subservice_area,
			"product": row.product,
			"project": row.project,
		})
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
		args.update({
			"credit": total_asset_cost,
			"credit_in_account_currency": total_asset_cost,
			"credit_in_transaction_currency": total_asset_cost,
			"service_area": row.target_service_area if(row.target_service_area) else row.service_area,
			"subservice_area": row.target_subservice_area if(row.target_subservice_area) else row.subservice_area,
			"product": row.target_product if(row.target_product) else row.product,
			"project": row.target_project,
		})
			
		doc = frappe.get_doc(args)
		doc.insert(ignore_permissions=True)
		doc.submit()
	
	def change_asset_4_dimensions(row):
		service_area = row.target_service_area if(row.target_service_area) else row.service_area
		subservice_area = row.target_subservice_area if(row.target_subservice_area) else row.subservice_area
		product =  row.target_product if(row.target_product) else row.product
		frappe.db.sql(f"""
				Update `tabAsset`
				Set service_area = '{service_area}',
					subservice_area = '{subservice_area}',
					product = '{product}',
					project = '{row.target_project}'
				Where
					name = '{row.asset}'
				""")
		
	def process_asset_movement():
		args = get_gl_entry_dict(self)
		for row in self.assets:
			args.update({
	   			'against_voucher_type': 'Asset',
				'against_voucher': row.asset
			})
			default_asset_account(args, row)
			default_designated_asset_fund_account(args, row)
			make_depreciation_accouting_entries(args, row)
			change_asset_4_dimensions(row)

	process_asset_movement()

def get_gl_entry_dict(self):
	return frappe._dict({
		'doctype': 'GL Entry',
		'posting_date': getdate(self.transaction_date),
		'transaction_date': getdate(self.transaction_date),
		'against': f"Asset Movement: {self.name}",
		'voucher_type': 'Asset Movement',
		'voucher_no': self.name,
		'voucher_subtype': f'{self.purpose}, asset moved between branches. ',
		'company': self.company,
	})

# bench --site al-khidmat.com execute akf_accounts.utils.asset_gle_entry.inter_fund_transfer.get_depreciation_accouting_entries
def make_depreciation_accouting_entries(args, row):
	query = f"""
		Select 
			ds.journal_entry, ds.schedule_date, ds.accumulated_depreciation_amount
		From 
			`tabAsset Depreciation Schedule` ad inner join `tabDepreciation Schedule` ds on (ad.name=ds.parent)
		Where
			ad.docstatus=1
			and ifnull(ds.journal_entry, "")!=""
			and ad.company="{args.company}"
			and ad.asset="{row.asset}"
		Order By
			ds.schedule_date desc
		limit 1 """	
	
	asset_depreciation_schedule = frappe.db.sql(query, as_dict=1)
	cargs = get_currency_args()
	
	for row in asset_depreciation_schedule:
		query1 = f"""
			Select account, (case when debit>0 then "debit" else "credit" end) as sign,
		
			From `tabJournal Entry Account`
			Where docstatus = 1
			and parent = '{row.journal_entry}'
		"""
		jv_accounts= frappe.db.sql(query1, as_dict=1)
		after_depreciation_amount = (row.total_asset_cost - row.accumulated_depreciation_amount)
		for jv in jv_accounts:
			if(jv.sign == "debit"):
				args.update(cargs)
				args.update({
					"account": jv.account,
					"debit": after_depreciation_amount,
					"debit_in_account_currency": after_depreciation_amount,
					"debit_in_transaction_currency": after_depreciation_amount,
				})
			elif(jv.sign == "credit"):
				args.update(cargs)
				args.update({
					"account": jv.account,
					"credit": after_depreciation_amount,
					"credit_in_account_currency": after_depreciation_amount,
					"credit_in_transaction_currency": after_depreciation_amount,
				})	
			doc = frappe.get_doc(args)
			doc.insert(ignore_permissions=True)
			doc.submit()
