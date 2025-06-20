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
		console.log("paid_amount trigger fired");
		if (frm.doc.party_type == "Donor") {
			frm.doc.references.forEach(function (row) {
				// Only update the rate for items with category 'Electronics'
				frappe.model.set_value(row.doctype, row.name, 'allocated_amount', frm.doc.paid_amount);
			});

			frm.refresh_field('references');
		}
		updateRentSlabRate(frm);
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
	},
	custom_rent_slabs: function(frm) {
		if (frm.doc.custom_rent_slabs) {
			// Show custom_tax_payer_status field when checkbox is checked
			frm.set_df_property('custom_tax_payer_status', 'hidden', 0);
			frm.set_df_property('custom_supplier_type', 'hidden', 0);
			
			// Add row to taxes table if it doesn't exist
			let rent_slab_exists = false;
			frm.doc.taxes.forEach(function(tax) {
				if (tax.account_head === 'Rent Slab - AKFP') {
					rent_slab_exists = true;
				}
			});

			if (!rent_slab_exists) {
				frm.add_child('taxes', {
					charge_type: 'On Paid Amount',
					account_head: 'Rent Slab - AKFP',
					rate: 0
				});
				frm.refresh_field('taxes');
			}
		} else {
			// Hide fields when checkbox is unchecked
			frm.set_df_property('custom_tax_payer_status', 'hidden', 1);
			frm.set_df_property('custom_supplier_type', 'hidden', 1);
			
			// Remove rent slab row if exists
			let taxes = frm.doc.taxes || [];
			taxes = taxes.filter(function(tax) {
				return tax.account_head !== 'Rent Slab - AKFP';
			});
			frm.set_value('taxes', taxes);
			frm.refresh_field('taxes');
		}
	},
	custom_tax_payer_status: function(frm) {
		updateRentSlabRate(frm);
	},
	custom_supplier_type: function(frm) {
		updateRentSlabRate(frm);
	},
	taxes_add: function(frm, cdt, cdn) {
		console.log("taxes_add triggered for", cdt, cdn, locals[cdt][cdn]);
		let row = locals[cdt][cdn];
		if (row.account_head === 'Rent Slab - AKFP') {
			set_rent_slab_rate(frm, cdt, cdn);
		}
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

function updateRentSlabRate(frm) {
	// Only proceed if all required conditions are met
	if (!frm.doc.custom_rent_slabs || 
		!frm.doc.custom_tax_payer_status || 
		!frm.doc.custom_supplier_type || 
		!frm.doc.paid_amount) {
		console.log("Required fields missing:", {
			custom_rent_slabs: frm.doc.custom_rent_slabs,
			custom_tax_payer_status: frm.doc.custom_tax_payer_status,
			custom_supplier_type: frm.doc.custom_supplier_type,
			paid_amount: frm.doc.paid_amount
		});
		return;
	}

	console.log("Starting Rent Slab Rate update with values:", {
		custom_tax_payer_status: frm.doc.custom_tax_payer_status,
		custom_supplier_type: frm.doc.custom_supplier_type,
		paid_amount: frm.doc.paid_amount
	});

	// Fetch all Rent Slab documents (add filters if needed)
	frappe.call({
		method: 'frappe.client.get_list',
		args: {
			doctype: 'Rent Slab',
			fields: ['name'],
			limit_page_length: 100 // adjust as needed
		},
		callback: function(res) {
			if (res.message && res.message.length > 0) {
				let found = false;
				res.message.forEach(function(rent_slab_doc) {
					frappe.call({
						method: 'frappe.client.get',
						args: {
							doctype: 'Rent Slab',
							name: rent_slab_doc.name
						},
						callback: function(r) {
							if (r.message && r.message.slabs && r.message.slabs.length > 0) {
								const paid_amount = frm.doc.paid_amount;
								let matching_slab = null;
								r.message.slabs.forEach(function(slab) {
									console.log("Checking slab:", {
										from_amount: slab.from_amount,
										to_amount: slab.to_amount,
										tax_payer_status_id: slab.tax_payer_status_id,
										supplier_type_tax_payer_category: slab.supplier_type_tax_payer_category,
										percentage_deduction: slab.percentage_deduction
									});
									console.log("Comparing with:", {
										paid_amount: paid_amount,
										custom_tax_payer_status: frm.doc.custom_tax_payer_status,
										custom_supplier_type: frm.doc.custom_supplier_type
									});
									const amountMatch = paid_amount >= slab.from_amount && (!slab.to_amount || paid_amount <= slab.to_amount);
									const statusMatch = slab.tax_payer_status_id === frm.doc.custom_tax_payer_status;
									const supplierTypeMatch = slab.supplier_type_tax_payer_category === frm.doc.custom_supplier_type;
									console.log("Match results:", {
										amountMatch,
										statusMatch,
										supplierTypeMatch
									});
									if (amountMatch && statusMatch && supplierTypeMatch) {
										matching_slab = slab;
									}
								});
								if (matching_slab && !found) {
									found = true;
									console.log("Matching slab found:", matching_slab);
									let rent_slab_row = (frm.doc.taxes || []).find(tax => tax.account_head === 'Rent Slab - AKFP');
									if (rent_slab_row) {
										rent_slab_row.rate = matching_slab ? matching_slab.percent_deduction : 0;
										if (!rent_slab_row.description && rent_slab_row.account_head) {
											rent_slab_row.description = rent_slab_row.account_head.split(' - ').slice(0, -1).join(' - ');
										}
										console.log("Rent Slab row after update:", rent_slab_row);
										frm.refresh_field('taxes');
										if (frm.script_manager && frm.script_manager.trigger) {
											frm.script_manager.trigger("calculate_taxes_and_totals");
										}
									}
								}
							}
						}
					});
				});
				setTimeout(function() {
					if (!found) {
						console.log("No matching slab found. Setting rate to 0.");
						let rent_slab_row = (frm.doc.taxes || []).find(tax => tax.account_head === 'Rent Slab - AKFP');
						if (rent_slab_row) {
							rent_slab_row.rate = 0;
							if (!rent_slab_row.description && rent_slab_row.account_head) {
								rent_slab_row.description = rent_slab_row.account_head.split(' - ').slice(0, -1).join(' - ');
							}
							console.log("Rent Slab row after update:", rent_slab_row);
							frm.refresh_field('taxes');
							if (frm.script_manager && frm.script_manager.trigger) {
								frm.script_manager.trigger("calculate_taxes_and_totals");
							}
						}
					}
				}, 1000); // adjust delay as needed
			} else {
				console.log("No Rent Slab documents found.");
			}
		}
	});
}

function add_rent_slab_tax_row(frm, matching_slab) {
	// Remove any existing Rent Slab row first
	frm.doc.taxes = (frm.doc.taxes || []).filter(tax => tax.account_head !== 'Rent Slab - AKFP');

	// Add new row
	let new_row = frm.add_child('taxes', {
		charge_type: 'On Paid Amount',
		account_head: 'Rent Slab - AKFP',
		rate: 0
	});

	// Set the rate directly
	new_row.rate = matching_slab ? matching_slab.percent_deduction : 0;

	// Auto-set description if not set
	if (!new_row.description && new_row.account_head) {
		new_row.description = new_row.account_head.split(' - ').slice(0, -1).join(' - ');
	}

	console.log("Rent Slab row after setting rate and description:", new_row);

	frm.refresh_field('taxes');
	if (frm.script_manager && frm.script_manager.trigger) {
		frm.script_manager.trigger("calculate_taxes_and_totals");
	}
}

frappe.ui.form.on('Payment Entry Deduction', {
	account_head: function(frm, cdt, cdn) {
		let row = locals[cdt][cdn];
		if (row.account_head === 'Rent Slab - AKFP') {
			set_rent_slab_rate(frm, cdt, cdn);
		}
	}
});

function set_rent_slab_rate(frm, cdt, cdn) {
	let row = locals[cdt][cdn];
	frappe.call({
		method: 'frappe.client.get',
		args: {
			doctype: 'Rent Slab',
			name: frm.doc.custom_rent_slabs
		},
		callback: function(r) {
			if (r.message && r.message.slabs && r.message.slabs.length > 0) {
				const paid_amount = frm.doc.paid_amount;
				let matching_slab = null;
				r.message.slabs.forEach(function(slab) {
					const amountMatch = paid_amount >= slab.from_amount && (!slab.to_amount || paid_amount <= slab.to_amount);
					const statusMatch = slab.tax_payer_status_id === frm.doc.custom_tax_payer_status;
					const supplierTypeMatch = slab.supplier_type_tax_payer_category === frm.doc.custom_supplier_type;
					if (amountMatch && statusMatch && supplierTypeMatch) {
						matching_slab = slab;
					}
				});
				if (matching_slab) {
					console.log("Found matching slab:", matching_slab);
					let rent_slab_row = (frm.doc.taxes || []).find(tax => tax.account_head === 'Rent Slab - AKFP');
					if (rent_slab_row) {
						rent_slab_row.rate = matching_slab ? matching_slab.percent_deduction : 0;
						if (!rent_slab_row.description && rent_slab_row.account_head) {
							rent_slab_row.description = rent_slab_row.account_head.split(' - ').slice(0, -1).join(' - ');
						}
						console.log("Rent Slab row after update:", rent_slab_row);
						frm.refresh_field('taxes');
						if (frm.script_manager && frm.script_manager.trigger) {
							frm.script_manager.trigger("calculate_taxes_and_totals");
						}
					}
				} else {
					let rent_slab_row = (frm.doc.taxes || []).find(tax => tax.account_head === 'Rent Slab - AKFP');
					if (rent_slab_row) {
						rent_slab_row.rate = 0;
						if (!rent_slab_row.description && rent_slab_row.account_head) {
							rent_slab_row.description = rent_slab_row.account_head.split(' - ').slice(0, -1).join(' - ');
						}
						console.log("Rent Slab row after update:", rent_slab_row);
						frm.refresh_field('taxes');
						if (frm.script_manager && frm.script_manager.trigger) {
							frm.script_manager.trigger("calculate_taxes_and_totals");
						}
					}
				}
			}
		}
	});
}