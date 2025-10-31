import frappe
from frappe.utils import flt
from erpnext.assets.doctype.asset_capitalization.asset_capitalization import AssetCapitalization

class XAssetCapitalization(AssetCapitalization):
    def calculate_totals(self):
        super().calculate_totals()
        
        custom_pi_total = flt(self.custom_purchase_invoice_total or 0, self.precision("custom_purchase_invoice_total"))
        custom_se_total = flt(self.custom_stock_entry_total or 0, self.precision("custom_stock_entry_total"))
        
        self.total_value += custom_pi_total + custom_se_total
        self.total_value = flt(self.total_value, self.precision("total_value"))
        frappe.msgprint(f"Total Value after adding custom PI total: {self.total_value}")
        
        if self.target_qty:
            self.target_incoming_rate = self.total_value / self.target_qty

@frappe.whitelist()
def get_wip_composite_asset_pi_items(target_asset):
    """Get all Purchase Invoice Items for a WIP composite asset from submitted PIs"""
    items = frappe.db.sql("""
        SELECT 
            pi_item.item_code, 
            pi_item.amount, 
            pi_item.expense_account,
            pi_item.parent as invoice_id,
            pi_item.donor_desk, 
            pi_item.fund_class, 
            pi_item.service_area, 
            pi_item.subservice_area, 
            pi_item.product, 
            pi_item.cost_center,
            pi_item.transaction_type, 
            pi_item.inventory_scenario, 
            pi_item.project,
            pi_item.task, 
            pi_item.asset_category, 
            pi_item.donor_type, 
            pi_item.donation_type,
            pi_item.donor, 
            pi_item.reverse_donor, 
            pi_item.inventory_flag,
            pi_item.rejected_inventory_flag, 
            pi_item.from_inventory_flag,
            pi_item.from_inventory_donor,
            pi_item.from_inventory_product,
            pi_item.from_inventory_project,
            pi_item.from_inventory_intention,
            pi_item.from_inventory_donor_desk,
            pi_item.from_inventory_donor_type,
            pi_item.from_inventory_fund_class,
            pi_item.from_inventory_cost_center,
            pi_item.from_inventory_service_area,
            pi_item.from_inventory_asset_category,
            pi_item.from_inventory_subservice_area,
            pi_item.from_inventory_transaction_type,
            pi_item.from_product,
            pi_item.from_service_area,
            pi_item.from_subservice_area
        FROM `tabPurchase Invoice Item` pi_item
        INNER JOIN `tabPurchase Invoice` pi ON pi.name = pi_item.parent
        WHERE pi_item.wip_composite_asset = %s
        AND pi.docstatus = 1
        AND pi_item.parenttype = 'Purchase Invoice'
    """, target_asset, as_dict=1)
    
    return items


@frappe.whitelist()
def get_wip_composite_asset_se_items(target_asset):
    """Get all Stock Entry Items for a WIP composite asset from submitted SEs"""
    items = frappe.db.sql("""
        SELECT 
            se_item.item_code, 
            se_item.amount, 
            se_item.expense_account,
            se_item.parent as invoice_id,                          
            se_item.donor_desk, 
            se_item.fund_class, 
            se_item.service_area, 
            se_item.subservice_area, 
            se_item.product, 
            se_item.cost_center,
            se_item.transaction_type, 
            se_item.inventory_scenario, 
            se_item.project,
            se_item.task, 
            se_item.asset_category, 
            se_item.donor_type, 
            se_item.donation_type,
            se_item.donor, 
            se_item.reverse_donor, 
            se_item.inventory_flag
        FROM `tabStock Entry Detail` se_item
        INNER JOIN `tabStock Entry` se ON se.name = se_item.parent
        WHERE se_item.custom_wip_composite_asset = %s
        AND se.docstatus = 1
        AND se.stock_entry_type = 'Material Issue'
        AND se_item.parenttype = 'Stock Entry'
    """, target_asset, as_dict=1)
    
    return items

