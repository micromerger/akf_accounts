from frappe import _


def get_data():
	return {
		"fieldname": "material_request",
		"internal_links": {
			"Sales Order": ["items", "sales_order"],
			"Project": ["items", "project"],
			"Cost Center": ["items", "cost_center"],
		},
		"transactions": [
			{
				"label": _("Reference"),
				"items": ["Sales Order", "Request for Quotation", "Supplier Quotation", "Purchase Order"],
			},
			{"label": _("Stock"), "items": ["Purchase Receipt", "Pick List"]}, #"Stock Entry",  removed on request of Mobeen
			{"label": _("Manufacturing"), "items": ["Work Order"]},
			{"label": _("Internal Transfer"), "items": ["Sales Order"]},
			{"label": _("Accounting Dimensions"), "items": ["Project", "Cost Center"]},
		],
	}
