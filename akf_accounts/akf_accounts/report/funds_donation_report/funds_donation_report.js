// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.query_reports["Funds Donation Report"] = {
  filters: [
    {
      fieldname: "date",
      label: __("Date"),
      fieldtype: "Date",
      options: "",
    },
    {
      fieldname: "donor",
      label: __("Donor"),
      fieldtype: "Link",
      options: "Donor",
    },
    // {
    //   fieldname: "party_name",
    //   label: __("Fund/Class"),
    //   fieldtype: "Data",
    //   options: "",
    // },
    // {
    //   fieldname: "",
    //   label: __("Filter 4"),
    //   fieldtype: "",
    //   options: "",
    // },
    // {
    //   fieldname: "",
    //   label: __("Filter 5"),
    //   fieldtype: "",
    //   options: "",
    // },
  ],
};
