import frappe
from frappe.model.document import Document
from frappe.utils import get_link_to_form

class Donation(Document):
    def validate(self):
    #    self.set_donor_identity()
        self.validate_payment_details()
        self.fill_fields_payment_details_deduction_breakeve()
        self.validate_deduction_percentages()
    
    def validate_payment_details(self):
        if(len(self.payment_detail)<1):
            frappe.throw("Please provide, payment details to proceed further.")
    
    @frappe.whitelist()
    def set_donor_identity(self):
        if(self.donor_identity in ["Unknown", "Merchant"]):
            self.donor = "DONOR-2024-00004" # Unknown Donor
        else:
            if(self.donor == "DONOR-2024-00004"): self.donor = ""

    def fill_fields_payment_details_deduction_breakeve(self):
        for row1 in self.payment_detail:
            row1.payment_detail_id = row1.name
            for row2 in self.deduction_breakeven:
                if(row1.pay_service_area == row2.service_area and row1.project==row2.project):
                    row2.payment_detail_id = row1.name
              
    def verifications(self):
        msg= "Donor Identity, " if(not self.donor_identity) else ""
        msg+= "Contribution Type, " if(not self.contribution_type) else ""
        msg+= "Donor, " if(not self.donor) else ""
        # msg+= "Service Area, " if(not self.pay_service_area ) else ""
        msg+= "Donation Amount <b>(Amount>0)</b>, " if(self.total_donation<=0) else ""
        msg+= "Deduction Breakeven, " if(not self.deduction_breakeven) else ""
        msg+= "Receivable Account, " if(not self.receivable_account) else ""
        # msg+= "Fund Class, " if(not self.fund_class) else ""
        # msg+= "Cost Center, " if(not self.cost_center) else ""
        
        msg+= "Donation Receiving Method, " if(not self.donation_receiving_method) else ""
        msg+= "Transaction No/ Cheque No, " if(self.donation_receiving_method not in ["bank", "Bank"] and not self.transaction_no_cheque_no) else ""
        msg+= "Transaction No/ Cheque No, " if(self.donation_receiving_method in ["bank", "Bank"] and not self.cheque_leaf) else ""
        # msg+= "Paid Amount, " if(self.contribution_type=="Donation" and not self.paid_amount) else ""
        
        if(msg!=""):
            msg = "<b>Please enter details of:</b> " + msg
            frappe.throw(f"{msg}")
    
    @frappe.whitelist()
    def set_deduction_breakeven(self):
        self.set("deduction_breakeven", [])
        deduction_amount=0
        total_donation=0
        for row in self.payment_detail:
            total_donation+= row.donation_amount
            # Setup Deduction Breakeven
            temp_deduction_amount=0
            for args in frappe.db.sql("""
                SELECT 
                    company, income_type, account, percentage, min_percent, max_percent
                FROM 
                    `tabDeduction Details`
                WHERE 
                    ifnull(account, "")!=""
                    and parent = %s
                    and company = %s
                """, (row.program, self.company), as_dict=True):
                percentage_amount = 0
                if(row.donation_amount>0):
                    percentage_amount = row.donation_amount*(args.percentage/100)
                    temp_deduction_amount += percentage_amount
                args.update({
                    "donation_amount": row.donation_amount,
                    "amount": percentage_amount,
                    "service_area": row.program,
                    "project": row.project,
                    "cost_center": row.cost_center,
                    "payment_detail_id": row.name
                    })
                self.append("deduction_breakeven", args)

            row.deduction_amount = temp_deduction_amount    
            row.outstanding_amount = (row.donation_amount-row.deduction_amount)
            deduction_amount += temp_deduction_amount
            
        # calculate total
        self.total_donation = total_donation
        self.calculate_total(deduction_amount)
    
    @frappe.whitelist()
    def calculate_percentage(self):
        deduction_amount = 0
        for row in self.deduction_breakeven:
            amount = row.donation_amount*(row.percentage/100)
            row.amount = amount
            deduction_amount += amount
        # calculate totals
        self.calculate_total(deduction_amount)

    def calculate_total(self, deduction_amount):
        self.total_deduction = deduction_amount
        self.received_amount = self.total_donation
        self.amount_receivable = self.total_donation 
        self.outstanding_amount = (self.total_donation - deduction_amount)
        self.net_amount = (self.total_donation - deduction_amount)
    
    def set_accounts_detail(self):
        default = frappe.db.get_value("Accounts Default", {"parent": self.program}, ["receivable_account", "fund_class", "cost_center"], as_dict=1)
        if(default):
            self.receivable_account = default.receivable_account
            self.fund_class = default.fund_class
            self.cost_center = default.cost_center
        else:
            self.receivable_account = ""
            self.fund_class = ""
            self.cost_center = ""

    def validate_deduction_percentages(self):
        for row in self.get('deduction_breakeven'):
            if row.account:
                min_percentage, max_percentage = get_min_max_percentage(row.service_area, row.account)
                if min_percentage is not None and max_percentage is not None:
                    if row.percentage < min_percentage or row.percentage > max_percentage:
                        frappe.throw(f"Percentage for account '{row.account}' must be between {min_percentage}% and {max_percentage}%.")

    def on_submit(self):
        self.verifications()
        # 
        self.update_status()
        # Credit GL Entry
        self.make_payment_detail_gl_entry()
        self.make_deduction_gl_entries()
        # self.make_fund_class_gl_entry()
        # # Debit GL Entry
        self.make_receivable_gl_entry()
        # # It will make against receivable account
        self.make_payment_ledger_entry()
        # # It will make donation payment entry
        if(self.contribution_type=="Donation"):
            self.make_payment_entry()
    
    def update_status(self):
        self.db_set("status", "Unpaid")

    def get_gl_entry_dict(self):
        return frappe._dict({
            'doctype': 'GL Entry',
            'posting_date': self.posting_date,
            'transaction_date': self.posting_date,
            'against': f"Donation: {self.name}",
            'against_voucher_type': 'Donation',
            'against_voucher': self.name,
            'voucher_type': 'Donation',
            'voucher_no': self.name,
            'voucher_subtype': 'Receive',
            'remarks': self.instructions_internal,
            # 'is_opening': 'No',
            # 'is_advance': 'No',
            'company': self.company,
            # 'transaction_currency': "PKR",
            # 'transaction_exchange_rate': "1",
        })
    
    def make_payment_detail_gl_entry(self):
        args = self.get_gl_entry_dict()
        for row in self.payment_detail:
            if(not row.account): frappe.throw(f"[{row.doctype}]: <b>Row#{row.idx}</b>, please select account. ")
            args.update({
                # "party_type": "Donor",
                # "party": self.donor,
                "donor": row.donor,
                "program": row.pay_service_area,
                "subservice_area": row.subservice_area,
                "product": row.pay_product,
                "project": row.project,
                "cost_center": row.cost_center,
                "account": row.account,
                "debit": 0,
                "credit": row.donation_amount,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": row.donation_amount,
            })
            frappe.get_doc(args).submit()

    def make_deduction_gl_entries(self):
        args = self.get_gl_entry_dict()
        # Loop through each row in the child table `deduction_breakeven`
        for row in self.deduction_breakeven:
            args.update({
                "account": row.account,
                "cost_center": row.cost_center,
                "debit": 0,
                "credit": row.amount,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": row.amount,
                
            })
            frappe.get_doc(args).submit()

    def make_fund_class_gl_entry(self):
        if(not self.fund_class): frappe.throw("Please select `Fund Class` account in accounts detail.")
        args = self.get_gl_entry_dict()
        args.update({
            "account": self.fund_class,
            "debit": 0,
            "credit": self.net_amount,
            "debit_in_account_currency": 0,
            "credit_in_account_currency": self.net_amount
        })
        frappe.get_doc(args).submit()

    def make_receivable_gl_entry(self):
        if(not self.receivable_account): frappe.throw("Please select `Receivable Account` account in accounts detail.")
        args = self.get_gl_entry_dict()
        args.update({
            "account": self.receivable_account,
            'party_type' : "Donor",
            'party' : self.donor,
            "debit": self.outstanding_amount,
            "credit": 0,
            "debit_in_account_currency": self.outstanding_amount,
            "credit_in_account_currency": 0
        })
        frappe.get_doc(args).submit()

    def make_payment_ledger_entry(self):
        if(self.contribution_type!="Donation"): return
        if(not self.receivable_account): frappe.throw("Please enter `Receivable Account` in accounts detail.")
        for row in self.payment_detail:
            args = frappe._dict({
                "doctype": "Payment Ledger Entry",
                "posting_date": self.posting_date,
                "company": self.company,
                "account_type": "Receivable",
                "account": self.receivable_account,
                "party_type": "Donor",
                "party": self.donor,
                "due_date": self.received_date,
                "voucher_type": "Donation",
                "voucher_no": self.name,
                "against_voucher_type": "Donation",
                "against_voucher_no": self.name,
                "amount": row.donation_amount,
                "amount_in_account_currency": row.donation_amount,
                'remarks': self.instructions_internal,
            })
            frappe.get_doc(args).submit()

    def make_payment_entry(self):
        if(self.contribution_type!="Donation"): return
        if(not self.receivable_account): frappe.throw("Please enter `Receivable Account` in accounts detail.")
        for row in self.payment_detail:
            args = frappe._dict({
                "doctype": "Payment Entry",
                "payment_type" : "Receive",
                "party_type" : "Donor",
                "party" : self.donor,
                "party_name" : self.donor_name   ,
                "posting_date" : self.posting_date,
                "company" : self.company,
                "mode_of_payment" : self.donation_receiving_method,
                "reference_no" : self.transaction_no_cheque_no,
                "source_exchange_rate" : 0.3,
                "target_exchange_rate": 1,
                "paid_from" : self.receivable_account,
                "paid_to" : row.account,
                "reference_date" : self.received_date,
                "cost_center" : row.cost_center,
                "paid_amount" : row.donation_amount,
                "received_amount" : row.donation_amount,
                "program" : row.pay_service_area,
                "subservice_area" : row.pay_subservice_area,
                "product" : row.pay_product,
                "project" : row.project,
                "cost_center" : row.cost_center,
                "references": [{
                        "reference_doctype": "Donation",
                        "reference_name" : self.name,
                        "due_date" : self.posting_date,
                        "total_amount" : self.net_amount,
                        "outstanding_amount" : self.outstanding_amount,
                        "allocated_amount" : row.outstanding_amount,
                }]
            })
            doc = frappe.get_doc(args).submit()

    def before_cancel(self):
        self.del_gl_entries()
        self.del_payment_entry()
        self.del_payment_ledger_entry()
    
    def on_cancel(self):
        pass

    def del_gl_entries(self):
        if(frappe.db.exists({"doctype": "GL Entry", "docstatus": 1, "against_voucher": self.name})):
            frappe.db.sql(f""" delete from `tabGL Entry` Where against_voucher = "{self.name}" """)
    
    def del_payment_entry(self):
        payment = frappe.db.get_value("Payment Entry Reference", 
            {"docstatus": 1, "reference_doctype": "Donation", "reference_name":self.name},
            ["name", "parent"], as_dict=1)
        if(payment):
            frappe.db.sql(f""" delete from `tabPayment Entry Reference` Where name = "{payment.name}" """)
            frappe.db.sql(f""" delete from `tabPayment Entry` Where name = "{payment.parent}" """)
    
    def del_payment_ledger_entry(self):
        if(frappe.db.exists({"doctype": "Payment Ledger Entry", "docstatus": 1, "against_voucher_no": self.name})):
            frappe.db.sql(f""" delete from `tabPayment Ledger Entry` Where against_voucher_no = "{self.name}" """)
    
    
@frappe.whitelist()
def _make_payment_entry(source_name, target_doc=None):
    from frappe.model.mapper import get_mapped_doc
    def set_missing_values(source, target):
        target.naming_series = "ACC-PAY-.YYYY.-"
        target.payment_type = "Receive"
        # target.mode_of_payment = "Cheque"
        target.party_type = "Donor"
        target.party = source.donor
        target.party_name = source.donor_name
        target.cost_center = source.cost_center
        target.paid_from = source.receivable_account
        target.paid_amount = source.outstanding_amount
        target.base_paid_amount = source.outstanding_amount
        target.received_amount = source.outstanding_amount
        target.program = source.service_area
        # target.paid_from = source.receivable_account
        target.append("references", {
            "reference_doctype": "Donation",
            "reference_name": source_name,
            "due_date": source.received_date,
            "total_amount": source.donation_amount,
            "outstanding_amount": source.outstanding_amount,
            "allocated_amount": source.outstanding_amount,
            })

    doclist = get_mapped_doc(
    "Donation",
    source_name,
    {
        "Donation": {
            "doctype": "Payment Entry",
            # "validation": {"docstatus": ["=", 1]},
        }
    },
    target_doc,
    set_missing_values,
    )
    return doclist

@frappe.whitelist()
def get_min_max_percentage(program, account):
    result = frappe.db.sql("""
        SELECT min_percent, max_percent
        FROM `tabDeduction Details`
        WHERE parent = %s AND account = %s
    """, (program, account), as_dict=True)
    if result:
        return result[0].min_percent, result[0].max_percent
    else:
        return None, None

@frappe.whitelist()
def set_unknown_to_known(name, donor):
    
    """  
    => Update donor information in these doctypes.
        Donation
        Payment Detail [child table]
        GL Entry
        Payment Ledger Entry
        Payment Entry
    """ 
    if(not donor): frappe.throw("Please donor.")

    info = frappe.db.get_value("Donor", donor, "*", as_dict=1)

    frappe.db.sql(f""" 
        Update 
            `tabDonation`
        Set 
            reverse_donor = 'Unknown To Known', 
            donor = '{donor}', donor_name='{info.donor_name}', donor_type='{info.donor_type}', 
            donor_contact_no='{info.contact_no}',  donor_address= '{info.address}', email='{info.email}',
            city = '{info.city}'
        Where 
            docstatus=1
            and name = '{name}'
    """)

    frappe.db.sql(f""" 
        Update 
            `tabPayment Detail`
        Set 
            reverse_donor = 'Unknown To Known', 
            donor = '{donor}'
        Where 
            docstatus=1
            and parent = '{name}'
     """)

    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        party = '{donor}',
        donor = '{donor}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and ifnull(party, "")!=""
        and voucher_no = '{name}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        donor = '{donor}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and ifnull(party, "")=""
        and voucher_no = '{name}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabPayment Ledger Entry`
    Set 
        donor = '{donor}', reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and voucher_no = '{name}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabPayment Entry`
    Set 
        party = '{donor}', party_name= '{info.donor_name}', reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and name in  (select parent from `tabPayment Entry Reference` where reference_name ='{name}')
    """)

    frappe.msgprint("Donor detail updated in all accounting dimensions.", alert=1)

