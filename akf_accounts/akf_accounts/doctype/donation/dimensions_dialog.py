import frappe
from frappe.model.mapper import get_mapped_doc

@frappe.whitelist()
def make_donation_dialog(source_name, target_doc=None):
	# requested_item_qty = get_requested_item_qty(source_name)

	# def get_remaining_qty(so_item):
	# 	return flt(
	# 		flt(so_item.qty)
	# 		- flt(requested_item_qty.get(so_item.name, {}).get("qty"))
	# 		- max(
	# 			flt(so_item.get("delivered_qty"))
	# 			- flt(requested_item_qty.get(so_item.name, {}).get("received_qty")),
	# 			0,
	# 		)
	# 	)

    def update_item(source, target, source_parent):
        # qty is for packed items, because packed items don't have stock_qty field
        pass
		# target.project = source_parent.project
		# target.qty = get_remaining_qty(source)
		# target.stock_qty = flt(target.qty) * flt(target.conversion_factor)

		# args = target.as_dict().copy()
		# args.update(
		# 	{
		# 		"company": source_parent.get("company"),
		# 		"price_list": frappe.db.get_single_value("Buying Settings", "buying_price_list"),
		# 		"currency": source_parent.get("currency"),
		# 		"conversion_rate": source_parent.get("conversion_rate"),
		# 	}
		# )

		# target.rate = flt(
		# 	get_price_list_rate(args=args, item_doc=frappe.get_cached_doc("Item", target.item_code)).get(
		# 		"price_list_rate"
		# 	)
		# )
		# target.amount = target.qty * target.rate

    doc = get_mapped_doc(
        "Donation",
        source_name,
        {
            "Donation": {"doctype": "Donation", "validation": {"docstatus": ["=", 1]}},
            # "Packed Item": {
            # 	"doctype": "Material Request Item",
            # 	"field_map": {"parent": "sales_order", "uom": "stock_uom"},
            # 	"postprocess": update_item,
            # },
            "Payment Detail": {
                "doctype": "Program Details",
                # "field_map": {"name": "sales_order_item", "parent": "sales_order"},
                # "condition": lambda item: not frappe.db.exists(
                # 	"Product Bundle", {"name": item.item_code, "disabled": 0}
                # )
                # and get_remaining_qty(item) > 0,
                "postprocess": update_item,
            },
        },
        target_doc,
    )

    return doc