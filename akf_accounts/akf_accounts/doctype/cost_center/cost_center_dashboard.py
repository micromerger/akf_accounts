from frappe import _


def get_data():
	return {
		"fieldname": "cost_center",
		"reports": [{"label": _("Reports"), "items": ["Budget Variance Report", "General Ledger"]}],
		"transactions": [{"label": _("Internal Branch Info"), "items": ["Supplier", "Customer"]}],
	}
