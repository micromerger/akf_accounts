frappe.provide("erpnext.stock");
frappe.provide("erpnext.accounts.dimensions");
erpnext.landed_cost_taxes_and_charges.setup_triggers("Stock Entry");

frappe.ui.form.on("Funds Transfer", {
    onload_post_render: function(frm) {
        frm.get_field("funds_transfer_from").grid.set_multiple_add("ff_service_area");
        frm.refresh_field('funds_transfer_from');

        frm.get_field("funds_transfer_to").grid.set_multiple_add("ft_service_area");
        frm.refresh_field('funds_transfer_to');
    },
    onload: function(frm){
        var df = frappe.meta.get_docfield("Funds Transfer From","ff_cost_center", cur_frm.doc.name);
        df.read_only = 1;
        frm.refresh_field['funds_transfer_from']
    },

    refresh: function(frm) {
        set_query_service_area_transfer_from(frm);
        // set_query_service_area_transfer_to(frm);
        set_queries_funds_transfer_from(frm);
        set_queries_funds_transfer_to(frm);
        set_queries_transaction_types(frm);
      
        if (!frm.is_new() && frm.doc.docstatus < 2) {  
            set_custom_btns(frm);
        }
        frm.trigger("open_dimension_dialog"); // Nabeel Saleem, 12-03-2025
    },

    onload: function(frm) {
        $("#table_render").empty();
        $("#total_balance").empty();
        $("#previous").empty();
        $("#next").empty();
    },
    transaction_type: function(frm) {
        handle_transaction_type_logic(frm);
    },

    cost_center: function(frm) {
        // console.log("Custom Cost Center triggered");
        update_cost_center_in_both_children(frm);
    },

    from_bank_account: function(frm) {
        update_ff_bank_account_in_children(frm);
    },

    from_bank_account: function(frm) {
        update_ft_bank_account_in_children(frm);
    },

    from_cost_center: function(frm) {
       
        update_ff_cost_center_in_children(frm);
        
    },

    to_cost_center: function(frm) {
        update_ft_cost_center_in_children(frm);
        frm.call("set_deduction_breakeven");
    },
    open_dimension_dialog: function (frm) { // Nabeel Saleem, 12-03-2025
		if (!frm.doc.__islocal) {
			frappe.require("/assets/akf_accounts/js/customizations/dimension_dialog.js", function () {
				if (typeof make_dimensions_modal === "function" && (typeof donor_balance_set_queries === "function")) {
                    make_dimensions_modal(frm);
                    // donor_balance_set_queries(frm);
				} else {
					frappe.msgprint("Donation modal is not loaded.");
				}
				if ((typeof accounting_ledger === "function")) {
					if (frm.doc.docstatus == 1) {
						accounting_ledger(frm);
					}
				}
			});
		}
	}
});

function handle_transaction_type_logic(frm) {
    if (frm.doc.transaction_type === 'Inter Fund') {
        // console.log("Inside handle_transaction_type_logic Inter Fund ");
        
        frm.set_value('from_cost_center', '');
        frm.set_value('to_cost_center', '');
        frm.set_value('from_bank_account', '');
        frm.set_value('to_bank_account', '');
        frm.set_value('deduction_breakeven', []);
        frm.refresh_field("deduction_breakeven");
    } else if (frm.doc.transaction_type === 'Inter Branch') {
        // console.log("Inside handle_transaction_type_logic Inter Branch ");
        frm.set_value('cost_center', '');
        frm.call("set_deduction_breakeven");
    }
    
}

function update_ff_bank_account_in_children(frm) {
    const bank_account = frm.doc.from_bank_account;

    frm.doc.funds_transfer_from.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ff_account', bank_account);
    });

    frm.fields_dict['funds_transfer_from'].grid.grid_rows.forEach(row => {
        if (!row.doc.ff_account) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ff_account', bank_account);
        }
    });

    frm.refresh_field('funds_transfer_from');
}

function update_ft_bank_account_in_children(frm) {
    const bank_account = frm.doc.to_bank_account;

    frm.doc.funds_transfer_from.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ft_account', bank_account);
    });

    frm.fields_dict['funds_transfer_to'].grid.grid_rows.forEach(row => {
        if (!row.doc.ft_account) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ft_account', bank_account);
        }
    });

    frm.refresh_field('funds_transfer_to');
}

frappe.ui.form.on("Funds Transfer From", {
    project: function(frm, cdt, cdn) {
        // Trigger the get_html function whenever ff_donor is updated
        frm.call("donor_list_data_funds_transfer").then(r=>{});
    },
    ff_account: function(frm, cdt, cdn) {
        // Trigger the get_html function whenever ff_donor is updated
        frm.call("donor_list_data_funds_transfer").then(r=>{});
    },
    ff_donor: function(frm, cdt, cdn) {
        // Trigger the get_html function whenever ff_donor is updated
        frm.call("donor_list_data_funds_transfer").then(r=>{});
    },
    funds_transfer_from_add: function(frm, cdt, cdn) {
        const cost_center = frm.doc.cost_center; 
        const bank_account = frm.doc.from_bank_account;
        const from_costcenter = frm.doc.from_cost_center;

        const row = frappe.get_doc(cdt, cdn);
        if (frm.doc.transaction_type === 'Inter Fund') {
            // console.log("Funds Transfer From Inter Fund");
            frappe.model.set_value(row.doctype, row.name, "ff_cost_center", cost_center);
            frappe.model.set_value(row.doctype, row.name, "ff_account", bank_account);
            frm.fields_dict['funds_transfer_from'].grid.grid_rows_by_docname[cdn].toggle_editable('ff_cost_center', false);
        } else if (frm.doc.transaction_type === 'Inter Branch') {
            // console.log("Funds Transfer From Inter Branch");
            frappe.model.set_value(row.doctype, row.name, "ff_cost_center", from_costcenter);
            frappe.model.set_value(row.doctype, row.name, "ff_account", bank_account);
            frm.fields_dict['funds_transfer_from'].grid.grid_rows_by_docname[cdn].toggle_editable('ff_cost_center', false);
        }

       
        frm.refresh_field("funds_transfer_from");
    },
    ff_company: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let company = row.ff_company;

        frappe.model.set_value(cdt, cdn, 'ff_account', '');
        frappe.model.set_value(cdt, cdn, 'ff_cost_center', '');
        frappe.model.set_value(cdt, cdn, 'ff_service_area', '');
        frappe.model.set_value(cdt, cdn, 'ff_subservice_area', '');
        frappe.model.set_value(cdt, cdn, 'ff_product', '');
        frappe.model.set_value(cdt, cdn, 'project', '');
       
        frappe.call({
            method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_areas",
            args: {
                doc: frm.doc
            },
            callback: function(r) {
                // console.log("SERVICE AREA QUERY!!!");
                // console.log(r.message);  

                frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
                    var row = locals[cdt][cdn];
                    var company = row.ff_company;

                    if (!company) {
                        return {
                            filters: {
                                service_area: ["!=", ""]
                            }
                        };
                    }

                    return {
                        filters: {
                            company: company,
                            service_area: ["in", r.message]  
                        }
                    };
                };

                frm.refresh_field('funds_transfer_from'); // Corrected method call
            }
        });
    },

    ff_service_area: function (frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        if (row.ff_service_area) {
          row.ff_subservice_area = "";
          row.ff_product = "";
          row.project = "";
        }
        frm.refresh_field("funds_transfer_from")
    }
});


function get_balance_funds_tranfer_from(funds_transfer_from, row){
    // let ftrow = locals[cdt][cdn];
    let balance_amount = 0.0;
    let doctype, docname;
    let matched = true;
    funds_transfer_from.forEach(element => {
        doctype = element.doctype;
        docname = element.name;
        if((element.ff_donor== row.ft_donor) && (row.ft_amount<=element.ff_balance_amount) && matched){
            balance_amount += element.ff_balance_amount;
            matched = false;
            frappe.model.set_value(doctype, docname, 'ff_transfer_amount', row.ft_amount);
            frappe.model.set_value(doctype, docname, 'transfer', 1);
        }else if(element.ff_donor== row.ft_donor){
            frappe.model.set_value(doctype, docname, 'ff_transfer_amount', 0.0);
            frappe.model.set_value(doctype, docname, 'transfer', 0);
            matched = true;
        }
    });
    
    return  balance_amount;
}

frappe.ui.form.on("Funds Transfer To", {
    ft_donor: function(frm, cdt, cdn){
        frm.trigger()
    },
    ft_amount: function(frm, cdt, cdn) {
        frm.call("update_funds_tranfer_from");    
        setTimeout(() => {
            frm.call("set_deduction_breakeven");
        }, 200);
    },
    project: function(frm, cdt, cdn) {
        // frm.call("set_deduction_breakeven");
    },
    funds_transfer_to_add: function(frm, cdt, cdn) {

        const row = frappe.get_doc(cdt, cdn);

        function set_random_id(){
                if(frm.doc.is_return){ return; }
                let row = locals[cdt][cdn];
                row.random_id = Math.floor((1000 + row.idx) + (Math.random() * 9000));
                
        }
        const cost_center = frm.doc.cost_center;
        const bank_account = frm.doc.to_bank_account;
        const to_costcenter = frm.doc.to_cost_center;
        
        set_random_id();
        if (['Inter Fund', 'Inter Bank'].includes(frm.doc.transaction_type)) {
            // console.log("Funds Transfer From Inter Fund ");
            frappe.model.set_value(row.doctype, row.name, "ft_cost_center", cost_center);
            frappe.model.set_value(row.doctype, row.name, "ft_account", bank_account); 
            
        } else if (frm.doc.transaction_type === 'Inter Branch') {
            // console.log("Funds Transfer From Inter Branch ");
            frappe.model.set_value(row.doctype, row.name, "ft_cost_center", to_costcenter);
            frappe.model.set_value(row.doctype, row.name, "ft_account", bank_account); 
        }
        frm.refresh_field("funds_transfer_to")
    },
    ft_company: function(frm, cdt, cdn) {
        let row = locals[cdt][cdn];
        let company = row.ft_company;

        frappe.model.set_value(cdt, cdn, 'ft_account', '');
        frappe.model.set_value(cdt, cdn, 'ft_cost_center', '');
        frappe.model.set_value(cdt, cdn, 'ft_service_area', '');
        frappe.model.set_value(cdt, cdn, 'ft_subservice_area', '');
        frappe.model.set_value(cdt, cdn, 'ft_product', '');
        frappe.model.set_value(cdt, cdn, 'ft_project', '');
        
        /*frappe.call({
            method: "akf_accounts.akf_accounts.doctype.funds_transfer.funds_transfer.get_service_areas",
            args: {
                doc: frm.doc
            },
            callback: function(r) {
                // console.log("SERVICE AREA QUERY!!!");
                // console.log(r.message);  

                frm.fields_dict['funds_transfer_to'].grid.get_field('ft_service_area').get_query = function(doc, cdt, cdn) {
                    var row = locals[cdt][cdn];
                    var company = row.ft_company;

                    if (!company) {
                        return {
                            filters: {
                                service_area: ["!=", ""]
                            }
                        };
                    }

                    return {
                        filters: {
                            company: company,
                            service_area: ["in", r.message]  
                        }
                    };
                };

                frm.fields_dict['funds_transfer_to'].grid.refresh_field('ft_service_area');
            }
        });*/
    },
    ft_service_area: function (frm, cdt, cdn) {
        /*let row = locals[cdt][cdn];
        if (row.ft_service_area) {
          row.ft_subservice_area = "";
          row.ft_product = "";
          row.project = "";
        }
        frm.refresh_field("funds_transfer_to")*/
    }
    
});

frappe.ui.form.on('Deduction Breakeven', {
    percentage: function (frm, cdt, cdn) {
        // if(frm.doc.is_return){
        // frm.call("update_deduction_breakeven");
        // }else{
        frm.call("set_deduction_breakeven");
        // }
    },
});

function update_cost_center_in_both_children(frm) {
    const cost_center = frm.doc.cost_center;

    frm.doc.funds_transfer_to.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ft_cost_center', cost_center);
    });

    frm.fields_dict['funds_transfer_to'].grid.grid_rows.forEach(row => {
        if (!row.doc.ft_cost_center) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ft_cost_center', cost_center);
        }
    });

    frm.doc.funds_transfer_from.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ff_cost_center', cost_center);
    });

    frm.fields_dict['funds_transfer_from'].grid.grid_rows.forEach(row => {
        if (!row.doc.ff_cost_center) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ff_cost_center', cost_center);
        }
    });

    frm.refresh_field('funds_transfer_to');
    frm.refresh_field('funds_transfer_from');
}

function update_ff_cost_center_in_children(frm) {
    const cost_center = frm.doc.from_cost_center;

    frm.doc.funds_transfer_from.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ff_cost_center', cost_center);
    });

    frm.fields_dict['funds_transfer_from'].grid.grid_rows.forEach(row => {
        if (!row.doc.ff_cost_center) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ff_cost_center', cost_center);
        }
    });

    frm.refresh_field('funds_transfer_from');
}

function update_ft_cost_center_in_children(frm) {
    const cost_center = frm.doc.to_cost_center;

    frm.doc.funds_transfer_to.forEach(function(row) {
        frappe.model.set_value(row.doctype, row.name, 'ft_cost_center', cost_center);
    });

    frm.fields_dict['funds_transfer_to'].grid.grid_rows.forEach(row => {
        if (!row.doc.ft_cost_center) {
            frappe.model.set_value(row.doc.doctype, row.doc.name, 'ft_cost_center', cost_center);
        }
    });

    frm.refresh_field('funds_transfer_to');
}

function set_query_service_area_transfer_to(frm) {
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        var company = row.ft_company;

        if (!company) {
            return {
                filters: {
                    service_area: ["!=", ""]
                }
            };
        }

        return {
            filters: {
                company: company
            }
        };
    };
}

function set_custom_btns(frm) {
    frm.add_custom_button(__('Accounting Ledger'), function () {
        frappe.set_route("query-report", "General Ledger", {"voucher_no": frm.doc.name,"group_by": ""});
    }, __("View"));
}

function set_queries_transaction_types(frm) {
    frm.set_query("from_cost_center", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                name: ['!=', frm.doc.to_cost_center]
            }
        };
    });

    frm.set_query("to_cost_center", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company,
                name: ['!=', frm.doc.from_cost_center]
            }
        };
    });

    frm.set_query("cost_center", function() {
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: frm.doc.company  
            }
        };
    });

    frm.set_query("from_bank_account", function() {
        return {
            filters: {
                disabled: 0,
                is_group: 0,
                company: frm.doc.company,
                name: ['!=', frm.doc.to_bank_account]
            }
        };
    });

    frm.set_query("to_bank_account", function() {
        return {
            filters: {
                disabled: 0,
                is_group: 0,
                company: frm.doc.company,
                name: ['!=', frm.doc.from_bank_account]
            }
        };
    });

    frm.set_query("from_bank", function() {
        return {
            filters: {
                disabled: 0,
                is_group: 0,
                account_type: "Bank",
                company: frm.doc.company,
                
            }
        };
    });
    
    frm.set_query("to_bank", function() {
        return {
            filters: {
                disabled: 0,
                is_group: 0,
                account_type: "Bank",
                company: frm.doc.company,
               
            }
        };
    });
    
}

function set_queries_funds_transfer_from(frm) {
    set_query_cost_center_transfer_from(frm);
    set_query_subservice_area_transfer_from(frm);
    set_query_product_transfer_from(frm);
    set_query_project_transfer_from(frm);
    set_query_account_transfer_from(frm);
    set_query_ff_donor_transfer_from(frm);
}

function set_query_cost_center_transfer_from(frm) {
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_cost_center').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: row.ff_company
            }
        };
    };
}

function set_query_subservice_area_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ff_service_area === undefined
        ? { service_area: ["!=", undefined] }
        : { service_area: row.ff_service_area };

        return {
            filters: ffilters
        };
        };
    };

function set_query_product_transfer_from(frm) {
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ff_subservice_area === undefined
            ? { subservice_area: ["!=", undefined] }
            : { subservice_area: row.ff_subservice_area };

        return {
            filters: ffilters
        };
    };
}

function set_query_project_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                // company: frm.doc.company,
                custom_service_area: ["!=", ""],
                custom_service_area: row.ff_service_area,
                
            }
        };
    };
}

function set_query_account_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: row.ff_company,
                
                
            }
        };
    };
}

function set_query_ff_donor_transfer_from(frm){
    frm.fields_dict['funds_transfer_from'].grid.get_field('ff_donor').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active",
            }
        };
    };
}

function set_queries_funds_transfer_to(frm){
    set_query_cost_center(frm);
    set_query_subservice_area(frm);
    set_query_product(frm);
    set_query_project(frm);
    set_query_account(frm);
    set_query_ft_donor(frm);
 
}

function set_query_cost_center(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_cost_center').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: row.ft_company

            }
        };
    };
}

function set_query_service_area(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.subservice_area,
            }
        };
    };
}

function set_query_subservice_area(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_subservice_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        let ffilters = row.ft_service_area === undefined
        ? { service_area: ["!=", undefined] }
        : { service_area: row.ft_service_area };

        return {
            filters: ffilters
        };
        };
    };

function set_query_product(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_product').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                subservice_area: ["!=", ""],
                subservice_area: row.ft_subservice_area,
            }
        };
    };
}

function set_query_project(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                // company: frm.doc.company,
                custom_program: ["!=", ""],
                custom_program: row.ft_service_area,
                
            }
        };
    };
}

function set_query_account(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: row.ft_company,
                
                
            }
        };
    };
}

function set_query_ft_donor(frm){
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_donor').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                status: "Active",
            }
        };
    };
}

function set_cost_center_in_children(child_table, cost_center_field, cost_center) {
    let transaction_controller = new erpnext.TransactionController();
    transaction_controller.autofill_warehouse(child_table, cost_center_field, cost_center);
}

function set_query_service_area_transfer_from(frm) {
   /*  frm.fields_dict['funds_transfer_from'].grid.get_field('ff_service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        var company = row.ff_company;

        if (!company) {
            return {
                filters: {
                    service_area: ["!=", ""]
                }
            };
        }

        return {
            filters: {
                company: company
            }
        };
    }; */
}

function set_query_service_area_transfer_to(frm) {
    frm.fields_dict['funds_transfer_to'].grid.get_field('ft_service_area').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        var company = row.ft_company;

        if (!company) {
            return {
                filters: {
                    service_area: ["!=", ""]
                }
            };
        }

        return {
            filters: {
                company: company
            }
        };
    };
}

function format_currency(amount){
    const formattedAmount = amount.toLocaleString('en-US', {
        style: 'currency',
        currency: 'PKR'
    });
    return formattedAmount.replace('PKR', 'Rs.');
}


