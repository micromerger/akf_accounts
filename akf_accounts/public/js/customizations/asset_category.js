frappe.ui.form.on('Asset Category', {
    onload: function(frm) {
        frm.set_query('custom_designated_asset_fund_account', 'accounts', function(doc, cdt, cdn) {
			var d  = locals[cdt][cdn];
			return {
				"filters": {
					"account_type": "Fixed Asset",
					"root_type": "Asset",
					"is_group": 0,
					"company": d.company_name
				}
			};
		});
         frm.set_query('custom_income_account', 'accounts', function(doc, cdt, cdn) {
			var d  = locals[cdt][cdn];
			return {
				"filters": {
					"account_type": "Income Account",
					"root_type": "Income",
					"is_group": 0,
					"company": d.company_name
				}
			};
		});
    }
});