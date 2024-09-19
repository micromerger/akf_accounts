import frappe
from frappe import _
from frappe.utils import getdate
from erpnext.assets.doctype.asset.asset import Asset

from frappe.utils import (
	cint,
	today,
)

from erpnext.assets.doctype.asset.depreciation import (
    
    get_depreciable_asset_depr_schedules_data,
    get_depreciation_cost_center_and_depreciation_series_for_company,
    get_checks_for_pl_and_bs_accounts, 
    get_depreciation_accounts,
    get_credit_and_debit_accounts_for_asset_category_and_company,
    set_depr_entry_posting_status_for_failed_assets,
    notify_depr_entry_posting_error,
    get_depreciation_accounts,
    get_credit_and_debit_accounts)

class AssetExtendedClass(Asset):
    def validate(self):
        super().validate()
       
        if self.custom_source_of_asset_acquistion == "In Kind":
            if self.purchase_receipt:
                frappe.throw("Assets acquired 'In Kind' cannot have an associated Purchase Receipt, as they are donated directly.")
     
        elif self.custom_source_of_asset_acquistion == "Donation":
            if not self.purchase_receipt:  
                frappe.throw("Assets marked as 'Donation' must have an associated Purchase Receipt, as they are purchased.")
        
        else:
            pass
             
    def on_submit(self):
        super().on_submit()
        if self.custom_source_of_asset_acquistion == "In Kind":
            self.create_asset_gl_entries_in_kind()
        else:
             pass

    def create_asset_gl_entries_in_kind(self):
        donation_in_kind = frappe.db.get_value("Company", {"name": self.company}, "custom_default_donation_in_kind_account")
        designated_asset_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_designated_asset_fund_account")
        asset_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_asset_account")


        if not donation_in_kind or not designated_asset_fund_account:
            frappe.throw("Please set accounts")
            return
        
        current_date = today()

        gl_entry_asset_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': current_date,
            'transaction_date': current_date,
            'account': asset_account,
            'against_voucher_type': 'Asset',
            'against_voucher': self.name,
            'debit': self.gross_purchase_amount,
            'credit': 0.0,
            'account_currency': 'PKR',
            'debit_in_account_currency': self.gross_purchase_amount,
            'credit_in_account_currency': 0.0,
            'against': "Donation In Kind",
            'voucher_type': 'Asset',
            'voucher_no': self.name,
            'remarks': "Donation In Kind",
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': frappe.get_value("Fiscal Year", {"name": frappe.defaults.get_user_default("fiscal_year")}, "name"),
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': self.gross_purchase_amount,
            'credit_in_transaction_currency': 0.0,
            'transaction_exchange_rate': 1,
            'program': self.program,
            'party_type': 'Donor',
            'party': self.donor,
            'subservice_area': self.subservice_area,
            'donor': self.donor,
            'product': self.product
          
        })

        gl_entry_asset_account.insert(ignore_permissions=True)
        gl_entry_asset_account.submit()


        gl_entry_designated_fund_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': current_date,
            'transaction_date': current_date,
            'account': designated_asset_fund_account,
            'against_voucher_type': 'Asset',
            'against_voucher': self.name,
            'debit': 0.0,
            'credit': self.gross_purchase_amount,
            'account_currency': 'PKR',
            'debit_in_account_currency': 0.0,
            'credit_in_account_currency': self.gross_purchase_amount,
            'against': "Donation In Kind",
            'voucher_type': 'Asset',
            'voucher_no': self.name,
            'remarks': "Donation In Kind",
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': frappe.get_value("Fiscal Year", {"name": frappe.defaults.get_user_default("fiscal_year")}, "name"),
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': 0.0,
            'credit_in_transaction_currency': self.gross_purchase_amount,
            'transaction_exchange_rate': 1,
            'program': self.program,
            'party_type': 'Donor',
            'party': self.donor,
            'subservice_area': self.subservice_area,
            'donor': self.donor,
            'product': self.product
        })

        gl_entry_designated_fund_account.insert(ignore_permissions=True)
        gl_entry_designated_fund_account.submit()


        gl_entry_donation_in_kind_credit_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': current_date,
            'transaction_date': current_date,
            'account': donation_in_kind,
            'against_voucher_type': 'Asset',
            'against_voucher': self.name,
            'debit': 0.0,
            'credit': self.gross_purchase_amount,
            'account_currency': 'PKR',
            'debit_in_account_currency': 0.0,
            'credit_in_account_currency': self.gross_purchase_amount,
            'against': "Donation In Kind",
            'voucher_type': 'Asset',
            'voucher_no': self.name,
            'remarks': "Donation In Kind",
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': frappe.get_value("Fiscal Year", {"name": frappe.defaults.get_user_default("fiscal_year")}, "name"),
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': 0.0,
            'credit_in_transaction_currency': self.gross_purchase_amount,
            'transaction_exchange_rate': 1,
            'program': self.program,
            'party_type': 'Donor',
            'party': self.donor,
            'subservice_area': self.subservice_area,
            'donor': self.donor,
            'product': self.product
        })

        gl_entry_donation_in_kind_credit_account.insert(ignore_permissions=True)
        gl_entry_donation_in_kind_credit_account.submit()


        gl_entry_donation_in_kind_debit_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': current_date,
            'transaction_date': current_date,
            'account': donation_in_kind,
            'against_voucher_type': 'Asset',
            'against_voucher': self.name,
            'debit': self.gross_purchase_amount,
            'credit': 0.0,
            'account_currency': 'PKR',
            'debit_in_account_currency': self.gross_purchase_amount,
            'credit_in_account_currency': 0.0,
            'against': "Donation In Kind",
            'voucher_type': 'Asset',
            'voucher_no': self.name,
            'remarks': "Donation In Kind",
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': frappe.get_value("Fiscal Year", {"name": frappe.defaults.get_user_default("fiscal_year")}, "name"),
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': self.gross_purchase_amount,
            'credit_in_transaction_currency': 0.0,
            'transaction_exchange_rate': 1,
            'program': self.program,
            'party_type': 'Donor',
            'party': self.donor,
            'subservice_area': self.subservice_area,
            'donor': self.donor,
            'product': self.product
        })

        gl_entry_donation_in_kind_debit_account.insert(ignore_permissions=True)
        gl_entry_donation_in_kind_debit_account.submit()

        frappe.msgprint("GL Entries created successfully")



@frappe.whitelist()
def total_accumulated_depreciation(asset_name, gross_purchase_amount):
    query = """
        SELECT ds.accumulated_depreciation_amount
        FROM `tabDepreciation Schedule` ds
        JOIN `tabAsset Depreciation Schedule` ads ON ds.parent = ads.name
        WHERE ads.asset = %s AND ds.journal_entry IS NOT NULL
        ORDER BY ds.schedule_date ASC
        LIMIT 1;
    """
    result = frappe.db.sql(query, (asset_name,), as_dict=True)
    # frappe.msgprint(f"Query Result: {result}")

    depreciated_amount = result[0].get('accumulated_depreciation_amount', 0) if result else 0
    # frappe.msgprint(f"Depreciated Amount: {depreciated_amount}")

    
    try:
        gross_purchase_amount = float(gross_purchase_amount)
    except ValueError:
        frappe.throw("Invalid gross purchase amount")

    # current_asset_worth = gross_purchase_amount - depreciated_amount
    # frappe.msgprint(f"gross_purchase_amount: {gross_purchase_amount}")
    # frappe.msgprint(f"current_asset_worth: {current_asset_worth}")

    frappe.db.sql("""
        UPDATE `tabAsset`
        SET custom_current_asset_worth = %s
        WHERE name = %s
    """, (depreciated_amount, asset_name))
    
    return True


@frappe.whitelist()
def post_depreciation_entries_extended(date=None):
	# Return if automatic booking of asset depreciation is disabled
	if not cint(
		frappe.db.get_value("Accounts Settings", None, "book_asset_depreciation_entry_automatically")
	):
		return
	
	if not date:
		date = today()
		# date = "2024-10-31"
		# print(date)

	failed_asset_names = []
	error_log_names = []

	depreciable_asset_depr_schedules_data = get_depreciable_asset_depr_schedules_data(date)
	credit_and_debit_accounts_for_asset_category_and_company = {}
	depreciation_cost_center_and_depreciation_series_for_company = (
		get_depreciation_cost_center_and_depreciation_series_for_company()
	)

	accounting_dimensions = get_checks_for_pl_and_bs_accounts()
	

	for asset_depr_schedule_data in depreciable_asset_depr_schedules_data:
		(
			
			asset_depr_schedule_name,
			asset_name,
			asset_category,
			asset_company,
			sch_start_idx,
			sch_end_idx,
		) = asset_depr_schedule_data
		
		if (
			asset_category,
			asset_company,
		) not in credit_and_debit_accounts_for_asset_category_and_company:
		
			credit_and_debit_accounts_for_asset_category_and_company.update(
				{
					(
						asset_category,
						asset_company,
					): get_credit_and_debit_accounts_for_asset_category_and_company_extended(
						asset_category, asset_company
					),
					
				}
			)
			print("credit_and_debit_accounts_for_asset_category_and_company")
			print(credit_and_debit_accounts_for_asset_category_and_company)
			
		try:
			make_depreciation_entry_extended(
				asset_depr_schedule_name,
				date,
				sch_start_idx,
				sch_end_idx,
				credit_and_debit_accounts_for_asset_category_and_company[(asset_category, asset_company)],
				depreciation_cost_center_and_depreciation_series_for_company[asset_company],
				accounting_dimensions,
				
			)
			
			frappe.db.commit()
		except Exception as e:
			frappe.db.rollback()
			failed_asset_names.append(asset_name)
			error_log = frappe.log_error(e)
			error_log_names.append(error_log.name)

	if failed_asset_names:
		set_depr_entry_posting_status_for_failed_assets(failed_asset_names)
		notify_depr_entry_posting_error(failed_asset_names, error_log_names)

	frappe.db.commit()
	


def get_credit_and_debit_accounts_for_asset_category_and_company_extended(asset_category, company):
	(
		_,
		accumulated_depreciation_account,
		depreciation_expense_account,
	) = get_depreciation_accounts(asset_category, company)
	# #Added by Aqsa
	company = frappe.get_doc("Company", company)
	debit_account_designated_fund_account = company.custom_default_designated_asset_fund_account
	credit_account_income = company.custom_default_income
	#

	credit_account, debit_account = get_credit_and_debit_accounts(
		accumulated_depreciation_account, depreciation_expense_account
	)

	return (
        (credit_account, debit_account),
		#Added by Dev Aqsa
        (credit_account_income, debit_account_designated_fund_account)
		#
    )


@frappe.whitelist()
def make_depreciation_entry_extended(
    asset_depr_schedule_name,
    date=None,
    sch_start_idx=None,
    sch_end_idx=None,
    credit_and_debit_accounts=None,
    depreciation_cost_center_and_depreciation_series=None,
    accounting_dimensions=None,
):
    frappe.has_permission("Journal Entry", throw=True)

    if not date:
        date = today()
        # date = "2024-10-31"

    asset_depr_schedule_doc = frappe.get_doc("Asset Depreciation Schedule", asset_depr_schedule_name)
    asset = frappe.get_doc("Asset", asset_depr_schedule_doc.asset)

    if credit_and_debit_accounts:
        # Unpack both pairs of accounts
        (credit_account_1, debit_account_1), (credit_account_2, debit_account_2) = credit_and_debit_accounts
    else:
        (credit_account_1, debit_account_1), (credit_account_2, debit_account_2) = get_credit_and_debit_accounts_for_asset_category_and_company(
            asset.asset_category, asset.company
        )

    if depreciation_cost_center_and_depreciation_series:
        depreciation_cost_center, depreciation_series = depreciation_cost_center_and_depreciation_series
    else:
        depreciation_cost_center, depreciation_series = frappe.get_cached_value(
            "Company", asset.company, ["depreciation_cost_center", "series_for_depreciation_entry"]
        )

    depreciation_cost_center = asset.cost_center or depreciation_cost_center

    if not accounting_dimensions:
        accounting_dimensions = get_checks_for_pl_and_bs_accounts()

    depreciation_posting_error = None

    journal_entry_accounts = []

    for d in asset_depr_schedule_doc.get("depreciation_schedule")[
        sch_start_idx or 0 : sch_end_idx or len(asset_depr_schedule_doc.get("depreciation_schedule"))
    ]:
        try:
            journal_entry_accounts.extend([
                {
                    "account": debit_account_1,
                    "debit_in_account_currency": d.depreciation_amount,
                    "credit_in_account_currency": 0,
                    "cost_center": depreciation_cost_center,
                    "accounting_dimensions": accounting_dimensions,
                },
                {
                    "account": credit_account_1,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": d.depreciation_amount,
                    "cost_center": depreciation_cost_center,
                    "accounting_dimensions": accounting_dimensions,
                },
                {
                    "account": debit_account_2,
                    "debit_in_account_currency": d.depreciation_amount,
                    "credit_in_account_currency": 0,
                    "cost_center": depreciation_cost_center,
                    "accounting_dimensions": accounting_dimensions,
                },
                {
                    "account": credit_account_2,
                    "debit_in_account_currency": 0,
                    "credit_in_account_currency": d.depreciation_amount,
                    "cost_center": depreciation_cost_center,
                    "accounting_dimensions": accounting_dimensions,
                },
            ])
        except Exception as e:
            depreciation_posting_error = e

    if not depreciation_posting_error:
        # Create a single journal entry with all accounts
        journal_entry = frappe.get_doc({
            "doctype": "Journal Entry",
            "posting_date": date,
            "company": asset.company,
            "voucher_type": "Depreciation Entry",
            "accounts": journal_entry_accounts,
            "cost_center": depreciation_cost_center,
            "user_remark": f"Depreciation Entry for Asset: {asset.name}",
            "depreciation_entry": 1
        })
        journal_entry.insert(ignore_permissions=True)
        journal_entry.submit()

        asset.db_set("depr_entry_posting_status", "Successful")
        return asset_depr_schedule_doc

    raise depreciation_posting_error


# @frappe.whitelist()
# def update_date():
#      frappe.db.sql("""
#         UPDATE `tabPurchase Receipt` 
#         SET posting_date = '2024-09-17' 
#         WHERE name = 'MAT-PRE-2024-00552'
#     """)


@frappe.whitelist()
def update_date():
     frappe.db.sql("""
        UPDATE `tabAsset` 
        SET purchase_date = '2024-09-17' 
        WHERE name = 'ACC-ASS-2024-00179'
    """)