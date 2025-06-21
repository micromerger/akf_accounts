// Copyright (c) 2025, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Fund Class", {

    onload: function(frm) {
        // Set query for equity_account field in the child table
        frm.fields_dict["accounts_default"].grid.get_field("equity_account").get_query = function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            return {
                filters: {
                    account_type: "Equity",
                    disabled: 0,
                    company: row.company
                }
            };
        };
        // Set query for receivable_account field in the child table
        frm.fields_dict["accounts_default"].grid.get_field("receivable_account").get_query = function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            return {
                filters: {
                    account_type: "Receivable",
                    disabled: 0,
                    company: row.company
                }
            };
        };
        // Set query for cost_center field in the child table
        frm.fields_dict["accounts_default"].grid.get_field("cost_center").get_query = function(doc, cdt, cdn) {
            const row = locals[cdt][cdn];
            return {
                filters: {
                    is_group: 0,
                    disabled: 0,
                    company: row.company
                }
            };
        };
    },

    refresh: function(frm) {
        parent_doctype_set_queries(frm);
        
        if (!frm.is_new()) {
            // Add custom button to initiate Budget
            frm.add_custom_button(__('Budget'), function() {
                if (frm.is_new()) {
                    frm.save().then(() => {
                        initiate_budget(frm);
                    });
                } else {
                    initiate_budget(frm);
                }
            }, 'Initiate');
            
            // Add custom button to initiate Budget
            frm.add_custom_button(__('Project'), function() {
                if (frm.is_new()) {
                    frm.save().then(() => {
                        project_budget(frm);
                    });
                } else {
                    project_budget(frm);
                }
            }, 'Initiate');
            // Add custom button to transfer Budget
            frm.add_custom_button(__('Funds'), function() {
                if (frm.is_new()) {
                    frm.save().then(() => {
                        transfer_funds(frm);
                    });
                } else {
                    transfer_funds(frm);
                }
            }, 'Tansfer');
        }
        if (!frm.is_new()) {
            frm.trigger("open_dimension_dialog"); // Nabeel Saleem, 26-02-2025
        }
        // Load dashboard data
        if (!frm.is_new()) {
            loadFundClassDashboard(frm);
        }

        // Add click handler for stats section
        $('.dashboard-section .section-heading').on('click', function() {
            $(this).toggleClass('collapsed');
            $(this).next('.section-content').slideToggle();
        });
    },
    validate: function(frm) {
        frm.doc.deduction_details.forEach(function(row) {
            if (row.percentage < 0 || row.percentage > 100) {
                frappe.throw('Percentage should be between 0 and 100');
            }
            if (row.min_percent < 0 || row.min_percent > 100) {
                frappe.throw('Minimum Percentage should be between 0 and 100');
            }
            if (row.max_percent < 0 || row.max_percent > 100) {
                frappe.throw('Maximum Percentage should be between 0 and 100');
            }
            if (row.max_percent < row.min_percent) {
                frappe.throw('Maximum Percentage cannot be less than Minimum Percentage');
            }
            if (row.percentage < row.min_percent) {
                frappe.throw('Percentage cannot be less than Minimum Percentage');
            }
            if (row.percentage > row.max_percent) {
                frappe.throw('Percentage cannot be greater than Maximum Percentage');
            }
        });
    },
    service_area: function(frm) {
        // Clear subservice_area and product when service_area changes
        frm.set_value("subservice_area", "");
        frm.set_value("product", "");
        
        // Refresh the subservice_area field to update its options
        frm.refresh_field("subservice_area");
    },
    subservice_area: function(frm) {
        // Clear product when subservice_area changes
        frm.set_value("product", "");
        
        // Refresh the product field to update its options
        frm.refresh_field("product");
    },
    open_dimension_dialog: function(frm){ // Nabeel Saleem, 26-02-2025
		// if(frm.doc.budget_against=="Project" && frm.doc.encumbrance){
        if(!frm.is_new()){
			frappe.require("/assets/akf_accounts/js/customizations/fund_class_dimension_dialog.js", function() {
				if (typeof make_dimensions_modal === "function") {
					make_dimensions_modal(frm);
				} else if(frm.doc.encumbrance) {
					frappe.msgprint("Donation modal is not loaded.");
				}
				if ((typeof accounting_ledger === "function")){
                // || (typeof donor_balance_set_queries === "function") && frm.doc.encumbrance) {
					accounting_ledger(frm);
					// donor_balance_set_queries(frm);
				} 
			});
		}
        // }
	},

});


function parent_doctype_set_queries(frm){
    frm.set_query('service_area', function () {
        return {
            filters: {
                disabled: 0,
            }
        };
    });
    frm.set_query('subservice_area', function () {
        return {
            filters: {
                disabled: 0,
                service_area: frm.doc.service_area || ["!=", ""]
            }
        };
    });
    frm.set_query('product', function () {
        return {
            filters: {
                disabled: 0,
                subservice_area: frm.doc.subservice_area || ["!=", ""]
            }
        };
    });
}

frappe.ui.form.on('Accounts Default', {
    company: function(frm, cdt, cdn) {
        const row = locals[cdt][cdn];
        // Clear dependent fields when company changes
        row.equity_account = "";
        row.receivable_account = "";
        row.cost_center = "";
        frm.refresh_field("accounts_default");
    }
});

function initiate_budget(frm) {
    // Get current fiscal year
    frappe.call({
        method: 'frappe.client.get',
        args: {
            doctype: 'Fiscal Year',
            filters: {
                'disabled': 0
            }
        },
        callback: function(r) {
            if (r.message) {
                frappe.new_doc("Budget", {
                    budget_against: "Fund Class",    
                    company: "Alkhidmat Foundation Pakistan",
                    fund_class: frm.doc.name,
                    // budget_against_value: frm.doc.name,
                    fiscal_year: r.message.name
                }).then(doc => {
                    doc.insert().then(() => {
                        frappe.set_route("Form", "Budget", doc.name);
                    });
                });
            }
        }
    });
}

function project_budget(frm){
    // Call the same function that's used for the Donation button
    get_donations(frm);
    
}

function transfer_funds(frm){
    // Require the transfer funds file
    frappe.require("/assets/akf_accounts/js/customizations/fund_class_transfer_funds.js", function() {
        if (typeof get_funds === "function") {
            get_funds(frm);
        } else {
            frappe.msgprint("Transfer funds functionality is not loaded.");
        }
    });
}

function loadFundClassDashboard(frm) {
    frappe.call({
        method: 'akf_accounts.akf_accounts.doctype.fund_class.fund_class_dashboard.get_fund_class_stats',
        args: {
            fund_class: frm.doc.name
        },
        callback: function(r) {
            if (r.message) {
                const data = r.message;
                // console.log((data));
                frm.dashboard.refresh();
                
                // Add stats section
                frm.dashboard.add_section(
                    frappe.render_template('fund_class_dashboard_stats', data)
                );

                // Add click handler for stats section
                $('.dashboard-section .section-heading').on('click', function() {
                    $(this).toggleClass('collapsed');
                    $(this).next('.section-content').slideToggle();
                });

                // // Hide stats section by default
                // $('.dashboard-section .section-content').hide();
                // $('.dashboard-section .section-heading').addClass('collapsed');
            }
        }
    });
}


