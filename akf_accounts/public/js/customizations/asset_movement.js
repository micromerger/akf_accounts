frappe.ui.form.on('Asset Movement', {
    refresh: function (frm) {
      
        if (frm.doc.docstatus==1){
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route('query-report', 'General Ledger',
                { against_voucher_type: 'Asset', against_voucher: frm.doc.name, voucher_no: frm.doc.name });
        }, __("View"));

    }
}
});
