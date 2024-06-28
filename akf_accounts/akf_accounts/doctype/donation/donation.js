frappe.provide("erpnext.accounts");

const DI_LIST = ["Unknown", "Merchant"];

frappe.ui.form.on('Donation', {
    onload_post_render: function(frm) {
        frm.get_field("payment_detail").grid.set_multiple_add("pay_service_area");
        frm.refresh_field('payment_detail');
    },
    onload: function(frm) {
        erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
    },
    refresh: function (frm) {
        set_queries(frm);
        set_query_subservice_area(frm);
        set_custom_btns(frm);
    },
    donor_identity: function(frm){
        frm.trigger("unknown_donor");
    },
    unknown_donor: function(frm){
        if(DI_LIST.find(x=> x===frm.doc.donor_identity)){
            frm.set_value("contribution_type", "Donation");
            frm.set_value("donor", "DONOR-2024-00004");
            frm.set_df_property("contribution_type", "read_only", 1);
        }else{
            frm.set_df_property("contribution_type", "read_only", 0);
            frm.set_value("donor", null);
        }
    },
    company: function (frm) {
        // erpnext.accounts.dimensions.update_dimension(frm, frm.doctype);
        // frm.set_value('service_area', '');
        // frm.clear_table('deduction_breakeven');
    },
    subservice_area: function(frm){
    }
});

frappe.ui.form.on('Payment Detail', {
    pay_service_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.program = row.pay_service_area;
        row.donor =  frm.doc.donor
        frm.call("set_deduction_breakeven");        
    },
    pay_subservice_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.subservice_area = row.pay_subservice_area;
        set_query_product(frm);
    },
    pay_product: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        row.product = row.pay_product;
    },
    project: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if(row.pay_service_area!=undefined || row.pay_service_area!=""){
            frm.call("set_deduction_breakeven");
        }
    },
    donation_amount: function (frm, cdt, cdn) {
        frm.call("set_deduction_breakeven");
    },
    payment_detail_remove: function(frm){
        frm.call("set_deduction_breakeven");
    }
});

frappe.ui.form.on('Deduction Breakeven', {
    percentage: function (frm, cdt, cdn) {
        frm.call("calculate_percentage");
    },
    amount: function (frm, cdt, cdn) {
        // frm.call("calculate_percentage");
    },
    deduction_breakeven_remove: function (frm) {
        frm.call("calculate_percentage");
    }
});

/* CUSTOM BUTTONS ON TOP OF DOCTYPE */
function set_custom_btns(frm) {

    if(frm.doc.docstatus==1){ 
        if(frm.doc.donor_identity == "Merchant" && frm.doc.contribution_type==="Donation" && (frm.doc.reverse_donor==undefined)){
            frm.add_custom_button(__('Reverse Donor'), function () {
                let d = new frappe.ui.Dialog({
                    title: 'Known donor detail',
                    fields: [
                        {
                            label: 'Donor',
                            fieldname: 'donor',
                            fieldtype: 'Link',
                            options: "Donor"
                        }
                    ],
                    size: 'small', // small, large, extra-large 
                    primary_action_label: 'Submit',
                    primary_action(values) {
                        // console.log(values);
                        if(values){
                            frappe.call({
                                method: "akf_accounts.akf_accounts.doctype.donation.donation.set_unknown_to_known",
                                args:{
                                    name: frm.doc.name,
                                    donor: values.donor
                                },
                                callback: function(r){
                                    d.hide();
                                    frm.reload_doc()
                                }
                            });
                        }
                    }
                });
                d.show();
            });
        }
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route("query-report", "General Ledger", {"voucher_no": frm.doc.name});
        }, __("View"));
        if(frm.doc.status!="Paid"){
            if(frm.doc.contribution_type == "Pledge"){
                frm.add_custom_button(__('Payment Entry'), function () {
                    frappe.model.open_mapped_doc({
                        method: "akf_accounts.akf_accounts.doctype.donation.donation._make_payment_entry",
                        frm: cur_frm
                    })
                }, __("Create"));
            }
        }
    }
}
/* END CUSTOM BUTTONS ON TOP OF DOCTYPE */

/* APPLYING SET QUERIES */
function set_queries(frm) {
    // set query on Account in `Deduction Breakeven`
    frm.fields_dict['deduction_breakeven'].grid.get_field('account').get_query = function (doc, cdt, cdn) {
        return {
            filters: {
                root_type: 'Income',
                is_group: 0,
                company: frm.doc.company
            }
        };
    };

    frm.set_query('cheque_leaf', function () {
        return {
            filters: {
                status: 'On Hand'
            }
        };
    });

    frm.set_query('receivable_account', function () {
        return {
            filters: {
                account_type: 'Receivable',
                company: frm.doc.company,
                is_group: 0
            }
        };
    });

    frm.set_query('fund_class', function () {
        return {
            filters: {
                root_type: 'Equity',
                is_group: 0,
                company: frm.doc.company
            }
        };
    });

    frm.set_query('cost_center', function () {
        return {
            filters: {
                company: frm.doc.company
            }
        };
    });
    set_query_subservice_area(frm);
    set_query_product(frm);
    set_query_account(frm);
    set_query_project(frm);
}

function set_query_subservice_area(frm){
    frm.fields_dict['payment_detail'].grid.get_field('pay_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                service_area: ["!=", ""],
                service_area: row.pay_service_area,
            }
        };
    };
}
// Payment Detail
function set_query_product(frm){
    frm.fields_dict['payment_detail'].grid.get_field('pay_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.pay_subservice_area,
            }
        };
    };
}
// Payment Detail
function set_query_account(frm){
    frm.fields_dict['payment_detail'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
        // var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                company: ["!=", ""],
                company: frm.doc.company,
                root_type: "Equity",
                
            }
        };
    };
}
// Payment Detail
function set_query_project(frm){
    frm.fields_dict['payment_detail'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                custom_program: ["!=", ""],
                custom_program: row.pay_service_area,
            }
        };
    };
}
/* END APPLYING SET QUERIES */


 // if (frm.doc.custom_payment_status === "Paid") {
    //     frm.page.set_indicator('Paid', 'green');
    // } else {
    //     frm.page.set_indicator('Unpaid', 'red');
    // }