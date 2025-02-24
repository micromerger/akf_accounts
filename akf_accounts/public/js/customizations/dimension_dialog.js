

// dimensions.events = {
//     open_modal(frm){
//         console.log('working');
//     }
// }
function make_dimensions_modal(frm){
    if (frm.doc.docstatus == 0) {
        frm.add_custom_button(__('Donation'), () => get_donations(frm),
            __("Get Balances"));
    }
};

// events.get_donations
function get_donations(frm){
    
    const d = new frappe.ui.Dialog({
        title: __("Accounting Dimensions"),
        fields: [
            {
                label: __("Service Area"),
                fieldname: "service_area",
                fieldtype: "Link",
                options: "Service Area",
                reqd: 1,
                get_query(){
                    return{
                        filters:{
                            disabled: 0
                        }
                    }
                }
            },
            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },
            {
                label: __("Subservice Area"),
                fieldname: "subservice_area",
                fieldtype: "Link",
                options: "Subservice Area",
                reqd: 1,
                get_query(){
                    let service_area = d.fields_dict.service_area.value;
                    return{
                        filters:{
                            service_area: service_area
                        }
                    }
                }
            },
            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },
            {
                label: __("Product"),
                fieldname: "product",
                fieldtype: "Link",
                options: "Product",
                reqd: 1,
                get_query(){
                    let subservice_area = d.fields_dict.subservice_area.value;
                    return{
                        filters:{
                            subservice_area: subservice_area
                        }
                    }
                }
            },
            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },
            {
                label: __("Project"),
                fieldname: "project",
                fieldtype: "Link",
                options: "Project",
                reqd: 1,
                get_query(){
                    let service_area = d.fields_dict.service_area.value;
                    return{
                        filters:{
                            company: frm.doc.company,
                            custom_service_area: service_area
                        }
                    }
                }
            },
            {
                label: __(""),
                fieldname: "col_break",
                fieldtype: "Column Break",
            },
            {
                label: __("Get Balance"),
                fieldname: "get_balance",
                fieldtype: "Button",
                options: "",
                click(){
                    const filters = {
                        "service_area": d.fields_dict.service_area.value,
                        "subservice_area": d.fields_dict.subservice_area.value,
                        "product": d.fields_dict.product.value,
                        "project": d.fields_dict.project.value,
                        "cost_center": frm.doc.cost_center,
                        "company": frm.doc.company,
                    }
                    const data = get_financial_stats(filters);
                   // Update the donor_balance table's data
                    d.fields_dict.donor_balance.df.data = data;
                    // Refresh the child table grid to reflect the new data
                    d.fields_dict.donor_balance.grid.refresh();
                }
            },
            {
                label: __(""),
                fieldname: "section_donor_balance1",
                fieldtype: "Section Break",
            },
            {
                fieldname: "donor_balance",
                fieldtype: "Table",
                label: __("Donor Balance"),
                cannot_add_rows: true,
                in_place_edit: false,
                // data: [{'donation': 1, 'donor': 2, 'balance': 1000}],
                reqd: 1,
                fields: [
                    {
                        fieldname: "donor",
                        label: __("Donor"),
                        fieldtype: "Link",
                        options: "Donor",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "donor_name",
                        label: __("Donor Name"),
                        fieldtype: "Data",
                        options: "",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "account",
                        label: __("Account"),
                        fieldtype: "Link",
                        options: "Account",
                        in_list_view: 1,
                        read_only: 1,
                    },
                    {
                        fieldname: "balance",
                        label: __("Balance"),
                        fieldtype: "Currency",
                        in_list_view: 1,
                        read_only: 1,
                    }
                ],
                /* on_add_row: (idx) => {
                  // idx = visible idx of the row starting from 1
                  // eg. set `log_type` as alternating IN/OUT in the table on row addition
                    let data_id = idx - 1;
                    let logs = dialog.fields_dict.logs;
                    let log_type = (data_id % 2) == 0 ? "IN" : "OUT";
      
                    logs.df.data[data_id].log_type = log_type;
                    logs.grid.refresh();
                }, */
            },
            
            {
                label: __(""),
                fieldname: "html_message",
                fieldtype: "HTML",
            },
        ],
        primary_action: (values) => {
            const array = values.donor_balance;
            let details = [];
            
            if(frm.doc.cost_center==undefined){
                d.fields_dict.html_message.df.options = `<b style="color: red;">Please select cost center to proceed.<b>`;
                d.fields_dict.html_message.refresh();
                return
            }
            array.forEach(row => {
                if(row.__checked){
                    details.push({
                        "pd_cost_center": frm.doc.cost_center,
                        "pd_account": row.account,
                        "pd_service_area": values.service_area,
                        "pd_subservice_area": values.subservice_area,
                        "pd_product": values.product,
                        "pd_project": values.project,
                        "pd_donor": row.donor,
                        "actual_balance": row.balance,
                    });
                }
            });
            let description = '';
            if(details.length>0){
                const childkey =  ("custom_program_details" in frm.doc)? "custom_program_details": "program_details";
                frm.set_value(childkey, details);
                d.hide();
            }else{
                description =`<b style="color: red;">Please select a record to proceed.<b>`;
            }
            d.fields_dict.html_message.df.options = description;
            d.fields_dict.html_message.refresh();
         },
        primary_action_label: __("Add Program Detail"),
      });
      d.show();
      
}

function get_financial_stats(filters){
    let data = [];
    frappe.call({
        method: "akf_projects.customizations.overrides.project.financial_stats.get_donor_transactions",
        async: false,
        args: {
            filters: filters 
        },
        callback: function(r){
            data = r.message;
            console.log(data);
        }
    });
    return data
}

function accounting_ledger(frm) {
    if(frm.doc.docstatus == 1) {
        frm.add_custom_button(__('Accounting Ledger'), function () {
            frappe.set_route("query-report", "General Ledger", {"from_date": frm.doc.posting_date, "voucher_no": frm.doc.name });
        }, __("View"));
    }
}

function donor_balance_set_queries(frm){
    const childkey =  ("custom_program_details" in frm.doc)? "custom_program_details": "program_details";
    frm.fields_dict[childkey].grid.get_field('pd_service_area').get_query = function (doc, cdt, cdn) {
        return {
            filters: {
                disabled: 0,
            }
        };
    }

    frm.fields_dict[childkey].grid.get_field('pd_subservice_area').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pd_service_area == undefined ? { service_area: ["!=", undefined] } : { service_area: row.pd_service_area };
        return {
            filters: ffilters
        };
    }

    frm.fields_dict[childkey].grid.get_field('pd_product').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.pd_subservice_area == undefined ? { subservice_area: ["!=", undefined] } : { subservice_area: row.pd_subservice_area };
        return {
            filters: ffilters
        };
    };

    frm.fields_dict[childkey].grid.get_field('pd_project').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let service_area = row.pd_service_area == undefined ? ["!=", undefined] : row.pd_service_area;
        return {
            filters: {
                company: frm.doc.company,
                custom_service_area: service_area,
                custom_allocation_check: 0
            }
        };
    };

    frm.fields_dict[childkey].grid.get_field('pd_donor').get_query = function (doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active",
                default_currency: row.currency,
            }
        };
    };
}