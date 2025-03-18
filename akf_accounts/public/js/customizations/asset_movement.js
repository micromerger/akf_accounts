frappe.ui.form.on('Asset Movement', {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Accounting Ledger'), function () {
                frappe.set_route('query-report', 'General Ledger',
                    { against_voucher_type: 'Asset', against_voucher: frm.doc.name, voucher_no: frm.doc.name });
            }, __("View"));

        }
        frm.trigger("assets_set_queries");
    },
    assets_set_queries: function(frm){
        frm.fields_dict['assets'].grid.get_field('source_cost_center').get_query = function (doc, cdt, cdn) {
            return {
                filters: {
                    "is_group": 0,
                    "disabled": 0,
                    "company": frm.doc.company
                }
            };
        };
        frm.fields_dict['assets'].grid.get_field('in_transit_cost_center').get_query = function (doc, cdt, cdn) {
            return {
                filters: {
                    "is_group": 0,
                    "disabled": 0,
                    "company": frm.doc.company
                }
            };
        };
        frm.fields_dict['assets'].grid.get_field('target_cost_center').get_query = function (doc, cdt, cdn) {
            return {
                filters: {
                    "is_group": 0,
                    "disabled": 0,
                    "company": frm.doc.company
                }
            };
        };
    }
});
