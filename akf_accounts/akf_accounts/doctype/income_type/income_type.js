// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on("Income Type", {
    refresh: function(frm) {
        frm.set_query('account', function() {
            return {
                filters: {
                    company: frm.doc.company,
                    disabled: 0,
                    root_type: 'Income'
                }
            };
        });
    }
});
