import frappe

def validate_stock_entry(doc, method=None):
    if(hasattr(doc, 'donation')):
        if(doc.donation):
            stock_id = frappe.db.get_value("Stock Entry", {
                'docstatus': 1, 
                'donation': doc.donation
                }, 
            'name')
            if(stock_id):
                frappe.throw(f"You cannot make multiple stock entries against in kind donation.", 
                            title='In Kind Donation')