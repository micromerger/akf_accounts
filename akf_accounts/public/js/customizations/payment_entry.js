frappe.ui.form.on('Payment Entry', {
    refresh: function(frm) {
		frm.set_query("reference_doctype", "references", function() {
			let doctypes = [];

			if (frm.doc.party_type == "Customer") {
				doctypes = ["Sales Order", "Sales Invoice", "Journal Entry", "Dunning"];
			} else if (frm.doc.party_type == "Supplier") {
				doctypes = ["Purchase Order", "Purchase Invoice", "Journal Entry"];
			} else if (frm.doc.party_type == "Employee") {
				doctypes = ["Expense Claim", "Employee Advance", "Journal Entry"];
			}  else if (frm.doc.party_type == "Donor") {
				doctypes = ["Donation"];
			}else {
				doctypes = ["Journal Entry"];
			}

			return {
				filters: { "name": ["in", doctypes] }
			};
		});

		frm.set_query("reference_name", "references", function(doc, cdt, cdn) {
			const child = locals[cdt][cdn];
			const filters = {"docstatus": 1, "company": doc.company};
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
				filters["status"] = ["in", ("Unpaid", "Return")];
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
	},
	custom_cheque_leaf: function (frm) {
		frm.set_value("payment_type", "Pay");
		frm.set_value("reference_no", frm.doc.custom_cheque_leaf);
		frm.set_df_property("payment_type", "read_only", 1);
		frm.set_df_property("reference_no", "read_only", 1);
	
		if (frm.doc.custom_cheque_leaf == "") {
		  frm.set_df_property("payment_type", "read_only", 0);
		  frm.set_df_property("reference_no", "read_only", 0);
		  frm.set_value("reference_no", "");
		}
		
	},
	paid_amount: function(frm){
		if(frm.doc.party_type=="Donor"){
			frm.doc.references.forEach(function(row) {
				// Only update the rate for items with category 'Electronics'
					frappe.model.set_value(row.doctype, row.name, 'allocated_amount', frm.doc.paid_amount);
			});

			frm.refresh_field('references');
		}
	}
});

frappe.ui.form.on("Payment Entry Reference", {
	reference_name: function(frm, cdt, cdn) {
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
				callback: function(r, rt) {
					if (r.message) {
						$.each(r.message, function(field, value) {
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
	paid_from_func: function(frm){
		if(frm.doc.paid_from_account_currency==undefined || frm.doc.paid_from_account_currency==""){
			frm.trigger("paid_from")
		}
	}
}