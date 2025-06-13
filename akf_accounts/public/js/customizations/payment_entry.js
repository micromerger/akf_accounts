frappe.ui.form.on('Payment Entry', {
	refresh: function (frm) {
		frm.set_query("reference_doctype", "references", function () {
			let doctypes = [];

			if (frm.doc.party_type == "Customer") {
				doctypes = ["Sales Order", "Sales Invoice", "Journal Entry", "Dunning"];
			} else if (frm.doc.party_type == "Supplier") {
				doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			} else if (frm.doc.party_type == "Employee") {
				doctypes = ["Expense Claim", "Employee Advance", "Journal Entry"];
			} else if (frm.doc.party_type == "Donor") {
				doctypes = ["Donation"];
			} else {
				doctypes = ["Journal Entry"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});

		frm.set_query("reference_name", "references", function (doc, cdt, cdn) {
			const child = locals[cdt][cdn];
			const filters = { "docstatus": 1, "company": doc.company };
			const party_type_doctypes = ["Sales Invoice", "Sales Order", "Purchase Invoice",
				"Purchase Order", "Expense Claim", "Dunning", "Donation"];

			if (in_list(party_type_doctypes, child.reference_doctype)) {
				filters[doc.party_type.toLowerCase()] = doc.party;
			}

			if (child.reference_doctype == "Expense Claim") {
				filters["is_paid"] = 0;
			}

			if (child.reference_doctype == "Employee Advance") {
				filters["status"] = "Unpaid";
			}

			if (child.reference_doctype == "Donation") {
				filters["status"] = ["in", ["Paid", "Unpaid", "Return"]];
			}

			return {
				filters: filters
			};
		});

		frm.set_query("custom_cheque_leaf", function () {
			return {
				filters: {
					status: "On Hand",
					bank_account: frm.doc.bank_account,
					company: frm.doc.company,

				},
			};
		});
		triggers.paid_from_func(frm);

		if (frm.doc.docstatus == 1 && frm.doc.mode_of_payment == "Postdated Cheque") {
			frappe.call({
				method: 'frappe.client.get_list',
				args: {
					doctype: 'Payment Entry',
					filters: {
						custom_post_dated_cheque_entry: frm.doc.name,
						docstatus: 1
					},
					fields: ['name']
				},
				callback: function (response) {
					if (response.message.length > 0) {
						console.log('A Payment Entry with this Post Dated Cheque Entry already exists.')
					}
					else {
						frm.add_custom_button(__("Reverse Postdated Cheque"), function () {
							let d = new frappe.ui.Dialog({
								title: "Reverse Postdated Cheque",
								fields: [
									{
										label: "Bank Account",
										fieldname: "bank_account",
										fieldtype: "Link",
										options: "Account",
										reqd: 1,
										get_query: function () {
											return {
												filters: {
													company: frm.doc.company,
													account_type: ["in", ["Bank", "Cash"]],
													is_group: 0,
													account_currency: frm.doc.paid_from_account_currency
												}
											};
										}
									},
									{
										label: "Posting Date",
										fieldname: "posting_date",
										fieldtype: "Date",
										reqd: 1
									}
								],
								primary_action_label: "Submit",
								primary_action(values) {
									frappe.call({
										method: 'frappe.client.get',
										args: {
											doctype: 'Payment Entry',
											name: frm.doc.name
										},
										callback: function (response) {
											if (response.message) {
												let doc_data = response.message;
												doc_data.custom_post_dated_cheque_entry = doc_data.name

												delete doc_data.name;
												delete doc_data.creation;
												delete doc_data.modified;
												delete doc_data.owner;
												delete doc_data.references;

												// doc_data.references = frm.doc.references;
												doc_data.posting_date = values.posting_date
												doc_data.mode_of_payment = ""
												doc_data.paid_from = doc_data.paid_to
												doc_data.paid_to = values.bank_account

												frappe.call({
													method: 'frappe.client.insert',
													args: {
														doc: doc_data
													},
													callback: function (res) {
														if (res.message) {
															frappe.msgprint(__('Payment Entry created against Postdated Cheque, Successfully'));
															frappe.set_route('Form', 'Payment Entry', res.message.name);
														}
													}
												});
											}
										}
									});
									d.hide();
								}
							});
							d.show();
						}, __('Create'));
					}
				}
			});

		}
		frm.trigger("open_dimension_dialog");

		// Add set_query for tax_withholding_category
		frm.set_query('tax_withholding_category', function() {
			return {
				filters: {
					'custom_tax_type_id': frm.doc.custom_tax_type_id,
					'custom_tax_payer_status_id': frm.doc.custom_tax_payer_status_id,
					'custom_nature_id': frm.doc.custom_nature_id,
					'custom_tax_nature_id': frm.doc.custom_tax_nature_id,
					'custom_schedule': frm.doc.custom_schedule,
					'custom_authority': frm.doc.custom_authority,
				}
			};
		});
	},
	party: function(frm) {
		if (frm.doc.party_type === 'Supplier' && frm.doc.party) {
			fetchSupplierDetails(frm);
		} else {
			
		}
	},
	party_name: function(frm) {
		if (frm.doc.party_type === 'Supplier' && frm.doc.party_name) {
			fetchSupplierDetails(frm);
		} else {
			
		}
	},
	party_type: function(frm){
		// if(frm.doc.party_type == "Donor" && frm.doc.payment_type=="Pay"){
		if(frm.doc.mode_of_payment == "Cheque" && frm.doc.payment_type=="Pay"){
			frm.set_value("payment_type", "Pay");
			frm.set_value("reference_no", frm.doc.custom_cheque_leaf);

			frm.set_df_property("reference_no", "hidden", 1);
			frm.set_df_property("payment_type", "read_only", 1);
		}else{
			frm.set_value("reference_no", "");
			frm.set_df_property("payment_type", "read_only", 0);
			frm.set_df_property("reference_no", "hidden", 0);
		}
		// Clear all supplier related fields when party type changes
		clearSupplierFields(frm);
		
		// Clear party and party name if party type changes
		frm.set_value('party', '');
		frm.set_value('party_name', '');
	},
	custom_cheque_leaf: function (frm) {
		if ([undefined, ""].includes(frm.doc.custom_cheque_leaf)) {
			frm.set_value("reference_no", "");
		}else{
			frm.set_value("reference_no", frm.doc.custom_cheque_leaf);
		}
	},
	paid_amount: function (frm) {
		if (frm.doc.party_type == "Donor") {
			frm.doc.references.forEach(function (row) {
				// Only update the rate for items with category 'Electronics'
				frappe.model.set_value(row.doctype, row.name, 'allocated_amount', frm.doc.paid_amount);
			});

			frm.refresh_field('references');
		}
	},
	custom_retention_money_payable: function (frm) {
		frm.call("process_accounts_retention_flow");
	},
	custom_retention_amount: function (frm) {
		frm.call("calculate_retention_amount");
	},
	custom_advance_payment_by_accounting_dimension: function(frm){
		frm.trigger("open_dimension_dialog");
	},
	open_dimension_dialog: function(frm){
		if(frm.doc.docstatus<2 && !frm.doc.__islocal && frm.doc.custom_advance_payment_by_accounting_dimension){
			frappe.require("/assets/akf_accounts/js/customizations/dimension_dialog.js", function() {
				if (typeof make_dimensions_modal === "function" && frm.doc.docstatus==0) {
					make_dimensions_modal(frm);
					donor_balance_set_queries(frm);
				} else if(frm.doc.docstatus==0){
					frappe.msgprint("Donation modal is not loaded.");
				}
				if (((typeof accounting_ledger === "function") || (typeof donor_balance_set_queries === "function")) && frm.doc.docstatus==1) {
					accounting_ledger(frm);
				} 
				
			});
		}
	},
	// custom_tax_payer_category: function(frm) {
	// 	frm.set_value('tax_withholding_category', '');
	// 	frm.refresh_field('tax_withholding_category');
	// },
	custom_nature_id: function(frm) {
		frm.set_value('tax_withholding_category', '');
		frm.refresh_field('tax_withholding_category');
	},
	custom_tax_type_id: function(frm) {
		frm.set_value('tax_withholding_category', '');
		frm.refresh_field('tax_withholding_category');
	},
	custom_tax_nature_id: function(frm) {
		frm.set_value('tax_withholding_category', '');
		frm.refresh_field('tax_withholding_category');
	}
});

function update_tax_withholding_category(frm) {
	// Only proceed if all required fields are filled
	if (
		!frm.doc.custom_nature_id || 
		!frm.doc.custom_tax_type_id || 
		!frm.doc.custom_tax_nature_id) {
		return;
	}

	// Call server method to get filtered tax withholding categories
	frappe.call({
		method: 'akf_accounts.customizations.overrides.payment_entry.get_filtered_tax_withholding_categories',
		args: {
			tax_payer_category: frm.doc.custom_tax_payer_category,
			nature_id: frm.doc.custom_nature_id,
			tax_type_id: frm.doc.custom_tax_type_id,
			tax_nature_id: frm.doc.custom_tax_nature_id
		},
		callback: function(r) {
			if (r.message) {
				// Update the tax withholding category field options
				frm.set_df_property('tax_withholding_category', 'options', r.message);
				frm.refresh_field('tax_withholding_category');
			}
		}
	});
}

frappe.ui.form.on("Payment Entry Reference", {
	reference_name: function (frm, cdt, cdn) {
		let row = locals[cdt][cdn];

		if (row.reference_name && row.reference_doctype) {
			return frappe.call({
				method: "akf_accounts.customizations.overrides.payment_entry.get_reference_details",
				args: {
					reference_doctype: row.reference_doctype,
					reference_name: row.reference_name,
					party_account_currency: (frm.doc.payment_type == "Receive") ?
						frm.doc.paid_from_account_currency : frm.doc.paid_to_account_currency,
					donor: frm.doc.party
				},
				callback: function (r, rt) {
					if (r.message) {
						$.each(r.message, function (field, value) {
							frappe.model.set_value(cdt, cdn, field, value);
						})

						let allocated_amount = frm.doc.unallocated_amount > row.outstanding_amount ?
							row.outstanding_amount : frm.doc.unallocated_amount;

						frappe.model.set_value(cdt, cdn, "allocated_amount", allocated_amount);
						frm.refresh_fields();
					}
				}
			})
		}
	},
});

triggers = {
	paid_from_func: function (frm) {
		if (frm.doc.paid_from_account_currency == undefined || frm.doc.paid_from_account_currency == "") {
			frm.trigger("paid_from")
		}
	}
}

// Helper function to fetch supplier details
function fetchSupplierDetails(frm) {
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Supplier',
			name: frm.doc.party || frm.doc.party_name
		},
		callback: function(r) {
			if (r.message) {
				// Set the custom fields with values from supplier
				frm.set_value('custom_tax_payer_category_id', r.message.supplier_type);
				frm.set_value('custom_resident_type_id', r.message.custom_resident_type);
				
				// If party was selected, set party_name and vice versa
				if (frm.doc.party && !frm.doc.party_name) {
					frm.set_value('party_name', r.message.supplier_name);
				} else if (frm.doc.party_name && !frm.doc.party) {
					frm.set_value('party', r.message.name);
				}
			}
		}
	});
}

// Helper function to clear supplier related fields
function clearSupplierFields(frm) {
	frm.set_value('custom_tax_payer_category_id', '');
	frm.set_value('custom_resident_type_id', '');
}