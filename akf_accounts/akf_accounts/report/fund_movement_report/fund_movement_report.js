// Mubashir Bashir 17-03-2025

frappe.query_reports["Fund Movement Report"] = {
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
			"fieldname":"product",
			"label": __("Product"),
			"fieldtype": "Link",
			"options": "Product"
		},
		{
			"fieldname":"project",
			"label": __("Project"),
			"fieldtype": "Link",
			"options": "Project"
		},
		{
			"fieldname":"fiscal_year",
			"label": __("Fiscal Year"),
			"fieldtype": "Link",
			"options": "Fiscal Year",
			"reqd": 1,
			"default": ""
		},		
	],
	"onload": function(report) {
		setTimeout(() => {
			get_current_fiscal_year();
		}, 300);
	}
};

function get_current_fiscal_year() {
	let today = frappe.datetime.get_today();

	frappe.db.get_list("Fiscal Year", {
		filters: [
			["year_start_date", "<=", today],
			["year_end_date", ">=", today]
		],
		fields: ["name"],
		limit: 1
	}).then((res) => {
		if (res.length > 0) {
			let fiscal_year = res[0].name;
			console.log("Fiscal Year is", fiscal_year);

			// Ensure the filter is available before setting it
			setTimeout(() => {
				frappe.query_report.set_filter_value("fiscal_year", fiscal_year);
			}, 300);
		}
	});
}
