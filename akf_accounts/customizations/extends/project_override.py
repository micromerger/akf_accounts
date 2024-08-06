#dfds
import frappe
from frappe import _
from erpnext.projects.doctype.project.project import Project


class XProject(Project):
    def validate(self):
        super(XProject, self).validate()

        self.validate_payable()
    
    def validate_payable(self):
        if self.status == 'Financial Close':
            payable_balance = self.get_project_payable_balance()['balance']
            # frappe.msgprint(f"{payable_balance} payable Balance")
            if payable_balance > 0:
                frappe.throw(_(f'Cannot complete the project because the payable account balance {payable_balance} is pending.'))

    
    def get_project_payable_balance(self):
        payable_balance = 0
 
        gl_entries = frappe.get_all('GL Entry', filters={'project': self.name, 'docstatus': 1}, fields=['account', 'debit', 'credit'])

        for entry in gl_entries:
            account_type = frappe.db.get_value('Account', entry['account'], 'account_type')

            if account_type == 'Payable':
                payable_balance += entry['credit'] - entry['debit']

        return {'balance': payable_balance}
