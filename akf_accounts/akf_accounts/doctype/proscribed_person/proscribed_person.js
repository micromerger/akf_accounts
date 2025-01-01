// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt
let cnic_mask= "9999999999999";
let cnicRegix = /^\d{5}\d{7}\d{1}$/;

frappe.ui.form.on("Proscribed Person", {
	refresh(frm) {
        frm.trigger("cnic_masking");
	},
    cnic: function(frm) {
        frm.trigger("cnic_validation");
    },
    cnic_masking: function(frm){
        frm.fields_dict["cnic"].$input.mask(cnic_mask);
        frm.fields_dict["cnic"].$input.attr("placeholder", cnic_mask);
    },
    cnic_validation:function(frm){
        let cnicNo = frm.doc.cnic;
        if(cnicNo){
            if (!(cnicNo.match(cnicRegix)) || cnicNo.length != cnic_mask.length) {
                frm.set_df_property("cnic", "description", `<p style="color:red">Please enter valid CNIC</p>`);
            } else {
                frm.set_df_property("cnic", "description", "");
            }
        }
        else{
            frm.set_df_property("cnic", "description", "");
        }
    }
});