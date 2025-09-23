frappe.ui.form.on("Project", {
    refresh: function (frm) {
        loadFundsDashboard(frm);
    },
    onload_post_render: function (frm) {
        loadFundsDashboard(frm);
    },
});

function loadFundsDashboard(frm) {
	if (!frm.is_new()) {
		frappe.call({
			"method": "akf_accounts.customizations.overrides.cdoctype.project.financial_stats.get_transactions",
			"args": {
				filters:{"project": frm.doc.name,}
				// "total_fund_allocated": frm.doc.total_fund_allocated
			},
			callback: function (r) {
				const data = r.message;
				frm.dashboard.refresh();
				
				frm.dashboard.add_indicator(__('Total Allocation: {0}',
					[format_currency(data.total_allocation)]), 'green');
				
				// frm.dashboard.add_indicator(__('Pledge Amount: {0}',
				// 	[format_currency(data.total_pledge)]),
				// 	'yellow');
				frm.dashboard.add_indicator(__('Transfered Funds: {0}',
					[format_currency(data.transfered_funds)]),
					'grey');
				// frm.dashboard.add_indicator(__('Received Funds: {0}',
				// 	[format_currency(data.received_funds)]),
				// 	'green');
				frm.dashboard.add_indicator(__('Consumed Funds: {0}',
					[format_currency(data.total_purchase)]),
					'red');
				
				frm.dashboard.add_indicator(__('Remaining Amount: {0}',
					[format_currency(data.remaining_amount)]),
					'blue');
			}
		});
	}
}