import frappe, ast
from frappe.model.document import Document
from frappe.utils import get_link_to_form
from erpnext.accounts.utils import get_balance_on

class Donation(Document):
    def validate(self):
        self.validate_payment_details()
        self.validate_deduction_percentages()
        self.validate_pledge_contribution_type()
        self.set_payment_detail_id()
        # frappe.msgprint("Party Balance Triggered!")
        # party_balance= get_balance_on(party_type="Donor", party="DONOR-2024-00006", cost_center="Main - AKFP")
        # frappe.msgprint(frappe.as_json(party_balance))
    
    def validate_payment_details(self):
        if(len(self.payment_detail)<1):
            frappe.throw("Please provide, payment details to proceed further.")

    def validate_deduction_percentages(self):
        for row in self.get('deduction_breakeven'):
            if row.account:
                min_percentage, max_percentage = get_min_max_percentage(row.service_area, row.account)
                if min_percentage is not None and max_percentage is not None:
                    if row.percentage < min_percentage or row.percentage > max_percentage:
                        frappe.throw(f"Percentage for account '{row.account}' must be between {min_percentage}% and {max_percentage}%.")

    def validate_pledge_contribution_type(self):
        if(self.contribution_type!="Pledge"):
            msg = []
            for d in self.payment_detail:
                if(not d.mode_of_payment):
                    msg+=[" Mode of Payment"]
                if(not d.transaction_no_cheque_no and d.mode_of_payment!="Cash"):
                    msg+=["Transaction No/Cheque No"]
                if(not d.account_paid_to):
                    msg+=["Account Paid To"]
                if(msg): 
                    msg = f"<b>Row#{d.idx}:</b> {msg}"
                    frappe.throw(msg=f"{msg}", title="Payment Detail")

    def set_payment_detail_id(self):
        pass
        # for row1 in self.payment_detail:
        #     row1.payment_detail_id = row1.name
        #     row1.donor = row1.donor_id
        #     for row2 in self.deduction_breakeven:
        #         if(row1.pay_service_area == row2.service_area and row1.project==row2.project):
        #             row2.payment_detail_id = row1.name

    @frappe.whitelist()
    def set_deduction_breakeven(self):
        """ def set_unknown_donor(row):
            if(self.donor_identity in ["Unknown", "Merchant"]): 
                row.donor_id = "DONOR-2024-00004"
            elif(self.donor_identity in ["Known", ""]):
                if(row.donor_id == "DONOR-2024-00004"):
                    row.donor_id = None """
        
        def reset_mode_of_payment(row):
            if(self.contribution_type == "Pledge"):
                row.mode_of_payment = None
                row.account_paid_to = None
                row.transaction_no_cheque_no = ""

        def get_deduction_details(row):
            if(self.donation_type=="Zakat"): return []
            return frappe.db.sql(f"""
                    SELECT 
                        company, income_type, account, percentage, min_percent, max_percent
                    FROM 
                        `tabDeduction Details`
                    WHERE 
                        ifnull(account, "")!=""
                        and company = '{self.company}'
                        and parent = '{row.pay_service_area}'
                        and project = '{row.project}'
                    """, as_dict=True)
            
        self.set("deduction_breakeven", [])
        deduction_amount=0
        total_donation=0
        
        for row in self.payment_detail:
            # set_unknown_donor(row)
            reset_mode_of_payment(row)
            total_donation+= row.donation_amount
            # Setup Deduction Breakeven
            temp_deduction_amount=0
            # Looping
            for args in get_deduction_details(row):
                percentage_amount = 0
                if(row.donation_amount>0):
                    percentage_amount = row.donation_amount*(args.percentage/100)
                    temp_deduction_amount += percentage_amount
                args.update({
                    "donor": row.donor_id,
                    "program": row.pay_service_area,
                    "subservice_area": row.pay_subservice_area,
                    "product": row.product,
                    "program": row.pay_service_area,

                    "donation_amount": row.donation_amount,
                    "amount": percentage_amount,
                    "service_area": row.program,
                    "project": row.project,
                    # "cost_center": row.cost_center,
                    "cost_center": self.donation_cost_center,
                    "payment_detail_id": row.idx
                    })
                self.append("deduction_breakeven", args)
            row.cost_center = self.donation_cost_center
            row.deduction_amount = temp_deduction_amount    
            row.net_amount = (row.donation_amount-row.deduction_amount)
            row.outstanding_amount = row.donation_amount if(self.contribution_type=="Pledge") else row.net_amount
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

    def on_submit(self):
        # Credit Debit, GL Entry
        self.make_payment_detail_gl_entry()
        self.make_deduction_gl_entries()
        self.make_payment_ledger_entry()
        if(self.contribution_type=="Donation"):
            self.make_payment_entry()
        self.update_status()
    
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
            # 'remarks': self.instructions_internal,
            # 'is_opening': 'No',
            # 'is_advance': 'No',
            'company': self.company,
            # 'transaction_currency': "PKR",
            # 'transaction_exchange_rate': "1",
        })
    
    def make_payment_detail_gl_entry(self):
        args = self.get_gl_entry_dict()
        
        for row in self.payment_detail:
            # credit
            args.update({
                "party_type": "",
                "party": "",
                "donor": row.donor_id,
                "program": row.pay_service_area,
                "subservice_area": row.subservice_area,
                "product": row.pay_product if(row.pay_product) else row.product,
                "project": row.project,
                "cost_center": row.cost_center,
                "account": row.equity_account,
                "debit": 0,
                "credit": row.outstanding_amount,
                "debit_in_account_currency": 0,
                "credit_in_account_currency": row.outstanding_amount,
                "voucher_detail_no": row.name,
            })
            doc = frappe.get_doc(args)
            doc.save(ignore_permissions=True)
            doc.submit()
            # debit
            args.update({
                "party_type": "Donor",
                "party": row.donor_id,
                "account": row.receivable_account,
                "debit":row.donation_amount,
                "credit": 0,
                "debit_in_account_currency": row.donation_amount,
                "credit_in_account_currency": 0,
            })
            if(self.donor_identity == "Merchant - Known"): pass
            else:
                doc = frappe.get_doc(args)
                doc.save(ignore_permissions=True)
                doc.submit()
        
        if(self.donor_identity == "Merchant - Known"):
            args.update({
                "debit": self.total_donation,
                "debit_in_account_currency": self.total_donation
            })
            doc = frappe.get_doc(args)
            doc.save(ignore_permissions=True)
            doc.submit()

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
                
                "donor": row.donor,
                "program": row.program,
                "subservice_area": row.subservice_area,
                "product": row.product,

                "voucher_detail_no": row.name,
            })
            doc = frappe.get_doc(args)
            doc.save(ignore_permissions=True)
            doc.submit()

    def make_payment_ledger_entry(self):
        args = {}
        for row in self.payment_detail:
            args = frappe._dict({
                "doctype": "Payment Ledger Entry",
                "posting_date": self.posting_date,
                "company": self.company,
                "account_type": "Receivable",
                "account": row.receivable_account,
                "party_type": "Donor",
                "party": row.donor_id,
                "due_date": self.due_date,
                "voucher_type": "Donation",
                "voucher_no": self.name,
                "against_voucher_type": "Donation",
                "against_voucher_no": self.name,
                "amount": row.donation_amount,
                "amount_in_account_currency": row.donation_amount,
                # 'remarks': self.instructions_internal,
                "voucher_detail_no": row.name,
            })
            if(self.donor_identity == "Merchant - Known"):
                pass
            else:
                doc = frappe.get_doc(args)
                doc.save(ignore_permissions=True)
                doc.submit()
        if(self.donor_identity == "Merchant - Known"):
            args.update({
                "amount": self.total_donation,
                "amount_in_account_currency": self.total_donation
            })
            doc = frappe.get_doc(args)
            doc.save(ignore_permissions=True)
            doc.submit()

    def make_payment_entry(self):
        # if(self.contribution_type!="Donation"): return
        args = {}
        for row in self.payment_detail:
            args = frappe._dict({
                "doctype": "Payment Entry",
                "payment_type" : "Receive",
                "party_type" : "Donor",
                "party" : row.donor_id,
                "party_name" : row.donor_name,
                "posting_date" : self.posting_date,
                "company" : self.company,
                "mode_of_payment" : row.mode_of_payment,
                "reference_no" : row.transaction_no_cheque_no,
                "source_exchange_rate" : 0.3,
                "target_exchange_rate": 1,
                "paid_from" : row.receivable_account,
                "paid_to" : row.account_paid_to,
                "reference_date" : self.due_date,
                "cost_center" : row.cost_center,
                "paid_amount" : row.donation_amount,
                "received_amount" : row.donation_amount,
                "donor": row.donor_id,
                "program" : row.pay_service_area,
                "subservice_area" : row.pay_subservice_area,
                "product": row.pay_product if(row.pay_product) else row.product,
                "project" : row.project,
                "cost_center" : row.cost_center,
                "references": [{
                        "reference_doctype": "Donation",
                        "reference_name" : self.name,
                        "due_date" : self.posting_date,
                        "total_amount" : self.total_donation,
                        "outstanding_amount" : row.donation_amount,
                        "allocated_amount" : row.donation_amount,
                }]
            })
            if(self.donor_identity == "Merchant - Known"):
                pass
            else:
                doc = frappe.get_doc(args)
                doc.save(ignore_permissions=True)
                doc.submit()

        if(self.donor_identity == "Merchant - Known"):
            args.update({
                "paid_amount" : self.total_donation,
                "received_amount" : self.total_donation,
            })
            doc = frappe.get_doc(args)
            doc.save(ignore_permissions=True)
            doc.submit()

    def update_status(self):
        status = "Paid" if(self.contribution_type == "Donation") else "Unpaid"
        self.db_set("status", status)
        self.reload()

    def before_cancel(self):
        self.del_gl_entries()
        self.del_payment_ledger_entry()
        self.del_payment_entry()
        self.del_child_table()
        
    def on_cancel(self):
        self.del_gl_entries()
        self.del_payment_ledger_entry()
        self.del_payment_entry()
        self.del_child_table()

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
    
    def del_child_table(self):
        if(frappe.db.exists({"doctype": "Payment Detail", "docstatus": 1, "parent": self.name})):
            frappe.db.sql(f""" delete from `tabPayment Detail` Where docstatus= 1 and parent = "{self.name}" """)
        
        if(frappe.db.exists({"doctype": "Deduction Breakeven", "docstatus": 1, "parent": self.name})):
            frappe.db.sql(f""" delete from `tabDeduction Breakeven` Where docstatus= 1 and parent = "{self.name}" """)
 

@frappe.whitelist()
def get_donors_list(donation_id):
    result = frappe.db.sql(f""" select donor_id, idx from `tabPayment Detail` where paid = 0 and parent='{donation_id}' """, as_dict=0)
    donors_list = {d[0] for d in result} if(result) else []
    idx_list = {}
    for donor in donors_list:
        idx_list[donor] = sorted([r[1] for r in result if(r[0]==donor)])
    return {
        "donors_list": sorted(list(donors_list)) if(donors_list) else [],
        "idx_list": idx_list if(idx_list) else {},
    }

@frappe.whitelist()
def get_outstanding(filters):
    filters = ast.literal_eval(filters)
    return frappe.db.sql(""" select outstanding_amount from `tabPayment Detail` 
        where docstatus=1
        and parent = %(name)s and donor_id = %(donor_id)s and idx = %(idx)s """, filters)[0][0]

@frappe.whitelist()
def pledge_payment_entry(doc, values):
    from frappe.utils import getdate
    curdate = getdate()
    
    doc = frappe._dict(ast.literal_eval(doc))
    values = frappe._dict(ast.literal_eval(values))
    row = frappe.db.get_value('Payment Detail', {'parent': doc.name, 'donor_id': values.donor_id, "idx": values.serial_no}, ['*'], as_dict=1)
    
    if(not row): frappe.throw(f"You're paying more than donation amount.")
    args = frappe._dict({
        "doctype": "Payment Entry",
        "payment_type" : "Receive",
        "party_type" : "Donor",
        "party" : row.donor_id,
        "party_name" : row.donor_name,
        "posting_date" : curdate,
        "company" : doc.company,
        "mode_of_payment" : values.mode_of_payment,
        "reference_no" : values.cheque_reference_no,
        "source_exchange_rate" : 0.3,
        "target_exchange_rate": 1,
        "paid_from" : row.receivable_account,
        "paid_to" : values.account_paid_to,
        "reference_date" : curdate,
        "cost_center" : row.cost_center,
        "paid_amount" : values.paid_amount,
        "received_amount" : values.paid_amount,
        "program" : row.pay_service_area,
        "subservice_area" : row.pay_subservice_area,
        "product" : row.pay_product,
        "project" : row.project,
        "cost_center" : row.cost_center,
        "donor": row.donor_id,
        "references": [{
                "reference_doctype": "Donation",
                "reference_name" : doc.name,
                "due_date" : curdate,
                "total_amount" : doc.total_donation,
                "outstanding_amount" : values.paid_amount,
                "allocated_amount" : values.paid_amount,
        }]
    })
    doc = frappe.get_doc(args)
    doc.save(ignore_permissions=True)
    doc.submit()
    # frappe.throw(f"{row}")
    frappe.db.set_value("Payment Detail", row.name, "paid", values.paid)
    frappe.db.set_value("Payment Detail", row.name, "outstanding_amount", values.outstanding_amount)
    pe_link = get_link_to_form("Payment Entry", doc.name, "Payment Entry")
    frappe.msgprint(f"{pe_link} has been paid successfully!", alert=True)
    return doc.name

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
def set_unknown_to_known(name, values):
    
    """  
    => Update donor information in these doctypes.
        Donation
        Payment Detail [child table]
        GL Entry
        Payment Ledger Entry
        Payment Entry
    """ 
    import ast
    values = frappe._dict(ast.literal_eval(values))
    pid = frappe.db.get_value("Payment Detail", {"parent": name, "transaction_no_cheque_no": values.transaction_no_cheque_no}, ["name", "idx"], as_dict=1) 
    if(not pid): frappe.throw(f"Tansaction No/ Cheque No: {values.transaction_no_cheque_no}", title="Not Found")
    info = frappe.db.get_value("Donor", values.donor, "*", as_dict=1)

    # Update Payment Details
    frappe.db.sql(f""" 
        Update 
            `tabPayment Detail`
        Set 
            reverse_donor = 'Unknown To Known', 
            donor_id = '{info.name}', donor_name='{info.donor_name}',
            donor = '{info.name}',
            donor_type='{info.donor_type if (info.donor_type) else ""}', 
            contact_no='{info.contact_no if (info.contact_no) else "" }',  
            address= '{info.address if (info.address) else "" }', 
            email='{info.email if (info.email) else ""}',
            city = '{info.city if(info.city) else ""}'
        Where 
            docstatus=1
            and parent = '{name}'
            and name = '{pid.name}'
     """)

    # Update gl entry for debit
    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        party = '{info.name}',
        donor = '{info.name}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and ifnull(party, "")!=""
        and voucher_no = '{name}'
        and voucher_detail_no = '{pid.name}'
    """)

    # Update gl entry for credit
    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        donor = '{info.name}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and voucher_no = '{name}'
        and voucher_detail_no = '{pid.name}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabDeduction Breakeven`
    Set
        donor = '{info.name}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and payment_detail_id = '{pid.idx}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        donor = '{info.name}',
        reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and voucher_no = '{name}'
        and voucher_detail_no in (select name from `tabDeduction Breakeven` where docstatus=1 and payment_detail_id = '{pid.idx}')
    """)

    frappe.db.sql(f""" 
    Update 
        `tabPayment Ledger Entry`
    Set 
        donor = '{info.name}', party = '{info.name}', reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and voucher_no = '{name}'
        and voucher_detail_no = '{pid.name}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabPayment Entry`
    Set 
        party = '{info.name}', party_name= '{info.donor_name}', donor='{info.name}', reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and name in  (select parent from `tabPayment Entry Reference` where reference_name ='{name}')
        and reference_no = '{values.transaction_no_cheque_no}'
    """)

    frappe.db.sql(f""" 
    Update 
        `tabGL Entry`
    Set 
        party = '{info.name}', donor='{info.name}', reverse_donor = 'Unknown To Known'
    Where 
        docstatus=1
        and voucher_no in  (
            select name from `tabPayment Entry` 
                where name in (select parent from `tabPayment Entry Reference` where reference_name ='{name}')
                and reference_no = '{values.transaction_no_cheque_no}'
            )
    """)


    frappe.msgprint("Donor id, updated in [<b>Payment Detail, Deduction Breakeven, GL Entry, Payment Entry, Payment Ledger Entry</b>] accounting dimensions/doctypes.", alert=1)


