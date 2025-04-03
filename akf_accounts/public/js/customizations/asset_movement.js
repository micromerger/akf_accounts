frappe.ui.form.on('Asset Movement', {
    refresh: function (frm) {
        if (frm.doc.docstatus == 1) {
            frm.add_custom_button(__('Accounting Ledger'), function () {
                frappe.set_route('query-report', 'General Ledger',
                    { against_voucher_type: 'Asset', against_voucher: frm.doc.name, voucher_no: frm.doc.name });
            }, __("View"));

        }
        frm.trigger("assets_set_queries");
        frm.trigger("toggleTargetProjectRowWise");
    },
    assets_set_queries: function (frm) {
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

        frm.fields_dict['assets'].grid.get_field('target_subservice_area').get_query = function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            let ffilters = row.target_service_area == undefined ? { service_area: ["!=", undefined] } : { service_area: row.target_service_area };
            return {
                filters: ffilters
            };
        };
        frm.fields_dict['assets'].grid.get_field('target_product').get_query = function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            let ffilters = row.target_subservice_area == undefined ? { subservice_area: ["!=", undefined] } : { subservice_area: row.target_subservice_area };
            return {
                filters: ffilters
            };
        };
        frm.fields_dict['assets'].grid.get_field('target_project').get_query = function (doc, cdt, cdn) {
            let row = locals[cdt][cdn];
            return {
                filters: {
                    "status": "Open",
                    "name": ["!=", row.project]
                }
            };
        }; 
        frm.fields_dict['assets'].grid.get_field('target_project').get_query = function (doc, cdt, cdn) {
            var row = locals[cdt][cdn];
            let service_area = row.target_service_area == undefined ? ["!=", undefined] : row.target_service_area;
            return {
                filters: {
                    "status": "Open",
                    "name": ["!=", row.project],
                    company: frm.doc.company,
                    custom_service_area: service_area,
                    custom_allocation_check: 0
                }
            };
        };
       
    },
    purpose: (frm) => {
        frm.trigger("toggleTargetProjectRowWise");
    },
    toggleTargetProjectRowWise: (frm) => {
        // Iterate through each row in the child table
        if (frm.doc.docstatus > 0) { return }
        frm.doc.assets.forEach((row) => {
            if (frm.doc.purpose == 'Inter Fund Transfer') { // Replace with your condition
                frm.set_df_property('assets', 'read_only', 0, frm.doc.name, 'target_project', row.name);
            } else {
                row.target_project = "";
                frm.set_df_property('assets', 'read_only', 1, frm.doc.name, 'target_project', row.name);
            }
        });
        // Refresh the child table to apply the changes
        frm.refresh_field('target_project');
    }
});

frappe.ui.form.on('Asset Movement Item', {
    assets_add: (frm, cdt, cdn) => {
        const row = locals[cdt][cdn];
        showHideTargetProjectForSingleRow(frm, row);
    },
})

function showHideTargetProjectForSingleRow(frm, row) {
    const flag = frm.doc.purpose == 'Inter Fund Transfer' ? 0 : 1;
    frm.set_df_property('assets', 'read_only', flag, frm.doc.name, 'target_project', row.name);
}