//  Mubashir Bashir 31-10-2025

function fetchWIPCompositeAssetPiItems(frm) {
    if (frm.doc.capitalization_method !== "Choose a WIP composite asset" || !frm.doc.target_asset) {
        console.log('Conditions not met for fetching WIP composite asset items');
        return;
    }

    // Show loading indicator
    frm.dashboard.set_headline_alert('Fetching WIP composite asset items from Purchase Invoice...');

    frm.clear_table('custom_purchase_invoice_items');

    frappe.call({
        method: 'akf_accounts.customizations.extends.asset_capitalization_x.get_wip_composite_asset_pi_items',
        args: {
            target_asset: frm.doc.target_asset
        },
        callback: function(response) {
            frm.dashboard.clear_headline();
            
            if (response.message && response.message.length > 0) {
                console.log('Found', response.message.length, 'matching Purchase Invoice Items from Purchase Invoice');
                
                let total_amount = 0;
                // Populate custom_purchase_invoice_items table
                response.message.forEach(function(pi_item) {
                    let child = frm.add_child('custom_purchase_invoice_items');

                    total_amount += flt(pi_item.amount);
                    
                    // Map basic fields
                    child.item = pi_item.item_code;
                    child.amount = pi_item.amount;
                    child.wip_account = pi_item.expense_account;
                    child.invoice_id = pi_item.invoice_id;
                    
                    // Map all accounting dimensions fields
                    const accountingDimensionFields = [
                        'donor_desk', 'fund_class', 'service_area', 'subservice_area',
                        'product', 'cost_center', 'transaction_type', 'inventory_scenario',
                        'project', 'task', 'asset_category', 'donor_type', 'donation_type',
                        'donor', 'reverse_donor', 'inventory_flag', 'rejected_inventory_flag',
                        'from_inventory_flag', 'from_inventory_donor', 'from_inventory_product',
                        'from_inventory_project', 'from_inventory_intention', 'from_inventory_donor_desk',
                        'from_inventory_donor_type', 'from_inventory_fund_class', 'from_inventory_cost_center',
                        'from_inventory_service_area', 'from_inventory_asset_category', 'from_inventory_subservice_area',
                        'from_inventory_transaction_type', 'from_product', 'from_service_area', 'from_subservice_area'
                    ];
                    
                    accountingDimensionFields.forEach(field => {
                        if (pi_item[field] !== undefined) {
                            child[field] = pi_item[field];
                        }
                    });
                });

                frm.set_value('custom_purchase_invoice_total', total_amount);

                frm.refresh_field('custom_purchase_invoice_items');
                
                frappe.show_alert({
                    message: __('Successfully fetched {0} items from submitted Purchase Invoices', [response.message.length]),
                    indicator: 'green'
                });
                
            } else {
                console.log('No matching Purchase Invoice Items found');
            }
        },
        error: function(err) {
            frm.dashboard.clear_headline();
            
            console.error('Error fetching WIP composite asset items from Purchase Invoice:', err);
            frappe.msgprint({
                title: __('Error'),
                message: __('Error fetching WIP composite asset items from Purchase Invoice. Please try again.'),
                indicator: 'red'
            });
        }
    });
}

function fetchWIPCompositeAssetSeItems(frm) {
    if (frm.doc.capitalization_method !== "Choose a WIP composite asset" || !frm.doc.target_asset) {
        console.log('Conditions not met for fetching WIP composite asset items');
        return;
    }

    // Show loading indicator
    frm.dashboard.set_headline_alert('Fetching WIP composite asset items from Stock Entry...');

    frm.clear_table('custom_stock_entry_items');

    frappe.call({
        method: 'akf_accounts.customizations.extends.asset_capitalization_x.get_wip_composite_asset_se_items',
        args: {
            target_asset: frm.doc.target_asset
        },
        callback: function(response) {
            frm.dashboard.clear_headline();
            
            if (response.message && response.message.length > 0) {
                console.log('Found', response.message.length, 'matching Stock Entry Items');
                
                let total_amount = 0;
                // Populate custom_purchase_invoice_items table
                response.message.forEach(function(se_item) {
                    let child = frm.add_child('custom_stock_entry_items');

                    total_amount += flt(se_item.amount);
                    
                    // Map basic fields
                    child.item = se_item.item_code;
                    child.amount = se_item.amount;
                    child.wip_account = se_item.expense_account;
                    child.invoice_id = se_item.invoice_id;
                    
                    // Map all accounting dimensions fields
                    const accountingDimensionFields = [
                        'donor_desk', 'fund_class', 'service_area', 'subservice_area',
                        'product', 'cost_center', 'transaction_type', 'inventory_scenario',
                        'project', 'task', 'asset_category', 'donor_type', 'donation_type',
                        'donor', 'reverse_donor', 'inventory_flag'
                    ];
                    
                    accountingDimensionFields.forEach(field => {
                        if (se_item[field] !== undefined) {
                            child[field] = se_item[field];
                        }
                    });
                });

                frm.set_value('custom_stock_entry_total', total_amount);

                frm.refresh_field('custom_stock_entry_items');
                
                frappe.show_alert({
                    message: __('Successfully fetched {0} items from submitted Stock Entry', [response.message.length]),
                    indicator: 'green'
                });
                
            } else {
                console.log('No matching Stock Entry Items found');
            }
        },
        error: function(err) {
            frm.dashboard.clear_headline();
            
            console.error('Error fetching WIP composite asset items from Stock Entry:', err);
            frappe.msgprint({
                title: __('Error'),
                message: __('Error fetching WIP composite asset items from Stock Entry. Please try again.'),
                indicator: 'red'
            });
        }
    });
}

frappe.ui.form.on('Asset Capitalization', {
    refresh: function(frm) {
        frm.add_custom_button(__('Fetch WIP Composite Items'), function() {
            fetchWIPCompositeAssetPiItems(frm);
            fetchWIPCompositeAssetSeItems(frm);
        }, __('Actions'));
    },
    
    capitalization_method: function(frm) {
        if (frm.doc.capitalization_method !== "Choose a WIP composite asset") {
            frm.clear_table('custom_purchase_invoice_items');
            frm.refresh_field('custom_purchase_invoice_items');
            frm.set_value('custom_purchase_invoice_total', 0);
            frm.refresh_field('custom_purchase_invoice_total');

            frm.clear_table('custom_stock_entry_items');
            frm.refresh_field('custom_stock_entry_items');
            frm.set_value('custom_stock_entry_total', 0);
            frm.refresh_field('custom_stock_entry_total');
        }
    },
    
    target_asset: function(frm) {
        if (!frm.doc.target_asset) {
            frm.clear_table('custom_purchase_invoice_items');
            frm.refresh_field('custom_purchase_invoice_items');
            frm.set_value('custom_purchase_invoice_total', 0);
            frm.refresh_field('custom_purchase_invoice_total');

            frm.clear_table('custom_stock_entry_items');
            frm.refresh_field('custom_stock_entry_items');
            frm.set_value('custom_stock_entry_total', 0);
            frm.refresh_field('custom_stock_entry_total');
        }
    }
});
