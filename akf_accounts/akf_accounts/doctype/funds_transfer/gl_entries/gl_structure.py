import frappe
from erpnext.accounts.utils import (
    get_fiscal_year
)
from frappe.utils import (
    today
)

def get_gl_structure(self):
	fiscal_year = get_fiscal_year(today(), company=self.company)[0]
	return {
		'doctype': 'GL Entry',
		'posting_date': self.posting_date,
		'transaction_date': self.posting_date,
		'voucher_type': 'Funds Transfer',
		'voucher_no': self.name,
		'remarks': 'Funds Transferred',
		'is_opening': 'No',
		'is_advance': 'No',
		'fiscal_year': fiscal_year,
		'company': self.company,
		'account_currency': 'PKR',
		'transaction_currency': 'PKR',
		'transaction_exchange_rate': 1,
	}