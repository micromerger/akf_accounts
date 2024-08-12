import frappe
import json
from erpnext.accounts.doctype.sales_invoice.sales_invoice import SalesInvoice

class XSalesInvoice(SalesInvoice):
    def validate(self):
        frappe.msgprint(frappe.as_json("Validate Triggered from XSalesInvoice"))
    def on_submit(self):
        self.create_gl_entries_for_sales_disposal_sale_gain()

    def create_gl_entries_for_sales_disposal_sale_gain(self):
        inventory_account = frappe.db.get_value("Company", {"name": self.company}, "custom_default_inventory_fund_account")
        frappe.msgprint(frappe.as_json(inventory_account))
        unrestricted_fund_account = frappe.db.get_value("Company",{"name": self.company}, "custom_default_unrestricted_fund_account")
        frappe.msgprint(frappe.as_json(unrestricted_fund_account))
