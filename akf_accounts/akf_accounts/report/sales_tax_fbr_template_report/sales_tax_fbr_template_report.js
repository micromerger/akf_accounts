// Developer Mubashir Bashir, -03-2025

frappe.query_reports["Sales tax-fbr template Report"] = {
	"filters": [
		{
			"fielname": "supplier",
			"label": __("Supplier"),
			"fieldtype": "Link",
			"options": "Supplier"
		},
		{
			"fielname": "from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
		},
		{
			"fielname": "to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
		},
	]
};
