import frappe


def updating_donation(self, cancelled=False):
    for row in self.references:
        if (row.reference_doctype == "Donation") and (row.outstanding_amount >= 0):
            outstanding_amount = updating_outstanding_amount(row, cancelled)
            updating_status(row, outstanding_amount)
            """  if(cancelled):
                # payment detail base-outstanding-amount
                details = frappe.db.get_value('Payment Detail', row.custom_donation_payment_detail, ['net_amount', 'outstanding_amount'], as_dict=1)
                if(details):
                    outstanding_amount = (details.outstanding_amount + row.allocated_amount)
                    frappe.db.set_value('Payment Detail', row.custom_donation_payment_detail, "outstanding_amount", outstanding_amount)
                    frappe.db.set_value('Payment Detail', row.custom_donation_payment_detail, "paid", 0)
                # end... """

def updating_outstanding_amount(row, cancelled):
    def payment_detail():
        payment_detail_id  = row.custom_donation_payment_detail
        outstanding_amount = 0.0
        if(payment_detail_id):
            data = get_payment_detail(payment_detail_id)
            if(cancelled):
                outstanding_amount = (data.outstanding_amount + row.allocated_amount)
            else:
                outstanding_amount = (data.outstanding_amount - row.allocated_amount)
            
            frappe.db.set_value("Payment Detail", payment_detail_id, 
                        "outstanding_amount", outstanding_amount)
    
    def donation():
        if(cancelled):
            outstanding_amount = (row.allocated_amount + row.outstanding_amount)
        else:
            outstanding_amount = (row.outstanding_amount - row.allocated_amount)
        
        frappe.db.set_value("Donation", row.reference_name, 
                "outstanding_amount", outstanding_amount)
        
        return outstanding_amount 
    
    payment_detail()
    return donation()

def updating_status(row, outstanding_amount):
    status = None
    if (outstanding_amount == 0 ):
        status = "Paid"
    elif(row.total_amount == outstanding_amount):
        status = "Unpaid"
    elif(outstanding_amount>0):
        status = "Partly Paid"
    if(frappe.db.exists(row.reference_doctype, {"docstatus": 1,"name": row.reference_name, "is_return": 1})):
        status = "Return"
    frappe.db.set_value("Donation", row.reference_name, "status", status)
        
def get_payment_detail(payment_detail_id):
    return frappe.db.get_value("Payment Detail", payment_detail_id, "*", as_dict=1)
