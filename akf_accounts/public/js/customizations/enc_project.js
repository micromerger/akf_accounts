frappe.ui.form.on("Project", {
    refresh: function(frm){
        if(!frm.is_new() && frm.doc.company){
            frappe.db.get_value("Company", frm.doc.company, "custom_enable_accounting_dimensions_dialog").then(r => {
                let is_enable_accounting_dimensions = r.message.custom_enable_accounting_dimensions_dialog;
                
                if(is_enable_accounting_dimensions){
                    frm.add_custom_button(__('Accounting Ledger'), function () {
                        frappe.set_route("query-report", "General Ledger", {"from_date": frm.doc.posting_date, "voucher_no": frm.doc.name });
                    }, __("View"));
                }
            })
        }
    }
});