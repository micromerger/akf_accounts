// Copyright (c) 2016, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
frappe.provide("erpnext.accounts.dimensions");

frappe.ui.form.on('Budget', {
	onload: function(frm) {
		frm.set_query("account", "accounts", function() {
			return {
				filters: {
					company: frm.doc.company,
					report_type: "Profit and Loss",
					is_group: 0
				}
			};
		});

		frm.set_query("monthly_distribution", function() {
			return {
				filters: {
					fiscal_year: frm.doc.fiscal_year
				}
			};
		});

		frm.set_query("project", function() {
			return {
				filters: {
					company: frm.doc.company,
				}
			};
		});

		erpnext.accounts.dimensions.setup_dimension_filters(frm, frm.doctype);
	},

	refresh: function(frm) {
		frm.trigger("toggle_reqd_fields");
		frm.trigger("open_dimension_dialog"); // Nabeel Saleem, 26-02-2025
		// frm.trigger("add_create_btns");
	},

	budget_against: function(frm) {
		frm.trigger("set_null_value");
		frm.trigger("toggle_reqd_fields");
		frm.trigger("open_dimension_dialog");
	},
	encumbrance: function(frm){
		frm.trigger("open_dimension_dialog");
	},
	set_null_value: function(frm) {
		if(frm.doc.budget_against == 'Cost Center') {
			frm.set_value('project', null)
		} else if(!frm.doc.encumbrance) {
			// console.log(frm.doc.encumbrance);
			frm.set_value('cost_center', null)
		}
	},

	toggle_reqd_fields: function(frm) {
		frm.toggle_reqd("cost_center", frm.doc.budget_against=="Cost Center");
		frm.toggle_reqd("project", frm.doc.budget_against=="Project");
	},

	open_dimension_dialog: function(frm){ // Nabeel Saleem, 26-02-2025
		if(frm.doc.budget_against=="Project" && frm.doc.encumbrance){
			frappe.require("/assets/akf_accounts/js/customizations/dimension_dialog.js", function() {
				if (typeof make_dimensions_modal === "function") {
					make_dimensions_modal(frm);
				} else if(frm.doc.encumbrance) {
					frappe.msgprint("Donation modal is not loaded.");
				}
				if ((typeof accounting_ledger === "function") || (typeof donor_balance_set_queries === "function") && frm.doc.encumbrance) {
					accounting_ledger(frm);
					donor_balance_set_queries(frm);
				} 
			});
		}
	},

	/*add_create_btns: function(frm){ // Nabeel Saleem, 27-02-2025
		if(frm.doc.docstatus == 1) {
			frm.add_custom_button(__('Material Request'), function () {
				frappe.model.open_mapped_doc({
					method: "akf_accounts.utils.encumbrance.enc_budget.make_material_request",
					frm: frm,
					// args: { default_supplier: values.default_supplier },
					run_link_triggers: true
				});
			}, __("Create"));
		}
	}*/
});
