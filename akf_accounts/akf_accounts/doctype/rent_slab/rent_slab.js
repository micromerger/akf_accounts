// Copyright (c) 2025, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Rent Slab", {
	refresh(frm) {
        frm.set_query('account_head', {
            'disabled': 0,
            'is_group': 0,
            'root_type': 'Liability',
            'account_type': 'Payable',
            'company': frm.doc.company,
            'name': ['like', '%Slab%']
        })
	},
});
