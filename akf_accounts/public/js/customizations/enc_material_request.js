frappe.ui.form.on("Material Request", {
    refresh: function(frm) {
        frm.trigger("open_dimension_dialog");
    },
	custom_encumbrance: function(frm) {
        frm.trigger("open_dimension_dialog");
    },
    open_dimension_dialog: function (frm) {
		if (!frm.is_new() && frm.doc.custom_encumbrance) {
			frappe.require("/assets/akf_accounts/js/customizations/dimension_dialog.js", function () {
				if (typeof make_dimensions_modal === "function" && (typeof donor_balance_set_queries === "function")) {
					if (!frm.doc.__islocal) {
						make_dimensions_modal(frm);
						// donor_balance_set_queries(frm);
					}
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
	},
});