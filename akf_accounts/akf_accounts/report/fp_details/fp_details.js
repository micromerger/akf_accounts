//  Mubashir Bashir 08-04-2025

frappe.query_reports["FP Details"] = {
	"filters": [
		{
			"fieldname":"company",
			"label": __("Company"),
			"fieldtype": "Link",
			"options": "Company",
			"default": frappe.defaults.get_user_default("Company"),
			"reqd": 1
		},
		{
			"fieldname":"cost_center",
			"label": __("Cost Center"),
			"fieldtype": "MultiSelectList",
			get_data: function(txt) {
				return frappe.db.get_link_options('Cost Center', txt, {
					company: frappe.query_report.get_filter_value("company")
				});
			}
		},
		{
			"fieldname":"service_area",
			"label": __("Service Area"),
			"fieldtype": "Link",
			"options": "Service Area"
		},
		{
			"fieldname":"subservice_area",
			"label": __("Subservice Area"),
			"fieldtype": "Link",
			"options": "Subservice Area"
		},
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname":"donor",
			"label": __("Donor"),
			"fieldtype": "Link",
			"options": "Donor"
		},
		{
			"fieldname":"donor_type",
			"label": __("Donor Type"),
			"fieldtype": "Link",
			"options": "Donor Type"
		},
		{
			"fieldname":"account",
			"label": __("Account"),
			"fieldtype": "Link",
			"options": "Account"
		},
		{
			"fieldname":"from_date",
			"label": __("From Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},	
		{
			"fieldname":"to_date",
			"label": __("To Date"),
			"fieldtype": "Date",
			"default": frappe.datetime.get_today(),
			"reqd": 1
		},	
	]
};

