import frappe
import json
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class XSalesInvoice(SalesInvoice):
    # def validate(self):
        # super().validate()
        # frappe.msgprint(frappe.as_json("Validate Triggered from XSalesInvoice"))
        # self.create_gl_entries_for_sales_disposal_sale_gain()

    def on_submit(self):
        super().on_submit()
        self.create_gl_entries_for_sales_disposal_sale_gain()

    def create_gl_entries_for_sales_disposal_sale_gain(self):
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        frappe.msgprint(frappe.as_json(inventory_account))
        unrestricted_fund_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_unrestricted_fund_account")
        frappe.msgprint(frappe.as_json(unrestricted_fund_account))

        gl_entry_unrestricted_fund_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': self.posting_date,
            'transaction_date': self.posting_date,
            'account': unrestricted_fund_account,
            'against_voucher_type': 'Sales Invoice',
            'against_voucher': self.name,
            'cost_center': 'Main - AKFP',
            'debit': 0.0,
            'credit': self.grand_total,
            'account_currency': 'PKR',
            'debit_in_account_currency': 0.0,
            'credit_in_account_currency': self.grand_total,
            'against': unrestricted_fund_account,
            'voucher_type': 'Sales Invoice',
            'voucher_no': self.name,
            'remarks': 'Sold Item',
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': '2024-2025',
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': 0.0,
            'credit_in_transaction_currency': self.grand_total,
            'transaction_exchange_rate': 1,
        })

        gl_entry_unrestricted_fund_account.insert(ignore_permissions=True)
        gl_entry_unrestricted_fund_account.submit()


        gl_entry_inventory_account = frappe.get_doc({
            'doctype': 'GL Entry',
            'posting_date': self.posting_date,
            'transaction_date': self.posting_date,
            'account': inventory_account,
            'against_voucher_type': 'Sales Invoice',
            'against_voucher': self.name,
            'cost_center': 'Main - AKFP',
            'debit': self.grand_total,
            'credit': 0.0,
            'account_currency': 'PKR',
            'debit_in_account_currency': self.grand_total,
            'credit_in_account_currency':  0.0,
            'against': unrestricted_fund_account,
            'voucher_type': 'Sales Invoice',
            'voucher_no': self.name,
            'remarks': 'Sold Item',
            'is_opening': 'No',
            'is_advance': 'No',
            'fiscal_year': '2024-2025',
            'company': self.company,
            'transaction_currency': 'PKR',
            'debit_in_transaction_currency': self.grand_total,
            'credit_in_transaction_currency':  0.0,
            'transaction_exchange_rate': 1,
        })

        gl_entry_inventory_account.insert(ignore_permissions=True)
        gl_entry_inventory_account.submit()

