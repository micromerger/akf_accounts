// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// Masks
let cnic= "99999-9999999-9";
let ntn = "999999-9";
let passport = "999999999";
let cnicRegix = /^\d{5}-\d{7}-\d{1}$/;
let ntnRegix = /^\d{6}-\d{1}$/;
let passportRegix = /^\d{9}$/;
// =>

let NoArrays = ['contact_no'];
/* mobile no validation */
var dial_code=null;
var phone_mask=null;
var phone_mask_length=0;
var phone_regix = null;
var mobileFieldName = null;
/* end.. */

frappe.ui.form.on('Donor', {
	refresh: function(frm) {
		frappe.dynamic_link = {doc: frm.doc, fieldname: 'name', doctype: 'Donor'};

		frm.toggle_display(['address_html','contact_html'], !frm.doc.__islocal);

		if(!frm.doc.__islocal) {
			frappe.contacts.render_address_and_contact(frm);
		} else {
			frappe.contacts.clear_address_and_contact(frm);
		}
        setQueryDesk(frm);
        set_query_donor_primary_address(frm);
        set_query_donor_primary_contact(frm);
        // Nabeel Saleem, 02-01-2025
        get_country_detail(frm);
		apply_mask_on_phones(frm);
		// End
        apply_mask_on_id_number(frm);
        
	},
    identification_type: function(frm){
        if(frm.doc.identification_type!="Others"){
            apply_mask_on_id_number(frm);
            
        }
        frm.set_value("cnic", "");
        frm.set_value("others", "");
    },
	cnic: function(frm) {
        // console.log(frm.doc.cnic)
        if (frm.doc.cnic && frm.doc.identification_type != "Other") {
            const labelName = __(frm.fields_dict['cnic'].df.label);
            if (!internationalIdNumberValidation(frm.doc.cnic, frm.doc.identification_type)) {
                // frm.set_value('cnic', '');
                frm.set_df_property("cnic", "description", `<p style="color:red">Please enter valid ${labelName}</p>`)
                // frm.set_intro(`Please enter valid ${labelName}`, 'red');
            }else{
				frm.set_df_property("cnic", "description", "")
			}
        }else{
			frm.set_df_property("cnic", "description", "")
		}
    },
    country: function(frm){
        get_country_detail(frm);
		apply_mask_on_phones(frm);
    },
    contact_no: function(frm){
		if(frm.doc.contact_no){
			const labelName = __(frm.fields_dict['contact_no'].df.label);
			if(!internationalPhoneValidation(frm.doc.contact_no, labelName)){
                frm.set_df_property('contact_no', 'description', `<p style="color:red">Please enter valid ${labelName}</p>`);
            }else{
                frm.set_df_property('contact_no', 'description', "");
            }
		}else{
            frm.set_df_property('contact_no', 'description', "");
        }
	},
    validate: function(frm){
		if(frm.doc.contact_no){
			const labelName = __(frm.fields_dict['contact_no'].df.label);
			internationalPhoneValidation(frm.doc.contact_no, labelName);
		}
	},
});


function setQueryDesk(frm){
    frm.set_query("donor_desk", function() {
        let ffilters = frm.doc.department == undefined ? { department: ["!=", undefined] } : { department: frm.doc.department };
        return {
            filters: ffilters
        };
    });
}

function set_query_donor_primary_address(frm){
    frm.set_query('donor_primary_address', function(doc) {
    return {
        filters: {
            'link_doctype': 'Donor',
            'link_name': doc.name
        }
    }
    });
}
function set_query_donor_primary_contact(frm){
    frm.set_query('donor_primary_contact', function(doc) {
        return {
            query: "akf_accounts.akf_accounts.doctype.donor.donor.get_donor_primary_contact",
            filters: {
                'donor': doc.name
            }
        }
    })
}

function apply_mask_on_id_number(frm) {
    let maskValue = "";
    frm.set_df_property("cnic", "label", frm.doc.identification_type);
    if(frm.doc.identification_type==="CNIC"){
        maskValue = cnic;
    }else if(frm.doc.identification_type==="NTN"){
        maskValue = ntn;
    }else if(frm.doc.identification_type==="Passport"){
        maskValue = passport;
    }
    
    frm.fields_dict["cnic"].$input.mask(maskValue);
    frm.fields_dict["cnic"].$input.attr("placeholder", maskValue);
    
}

function internationalIdNumberValidation(cnicNo, identification_type) {
    // var pattern = new RegExp("^\d{5}-\d{7}-\d{1}$");
    let pattern = identification_type=="NTN"? ntnRegix: (identification_type=="Passport"? passportRegix: cnicRegix);
    let masking = identification_type=="NTN"? ntn: (identification_type=="Passport"? passport: cnic);
    if (!(cnicNo.match(pattern)) || cnicNo.length != masking.length) {
        // frappe.msgprint(`Please enter valid ${labelName}`);
        return false;
    } else {
        return true;
    }
}

// Nabeel Saleem, 02-01-2025
/* 
Functions to apply international mobile phone (mask, regex)
*/
function get_country_detail(frm){
	if(!frm.doc.country) return
	frappe.call({
		method: "frappe.client.get_value",
		async: false,
		args: {
		  doctype: 'Country',
		  fieldname: ['custom_dial_code', 'custom_phone_mask', 'custom_phone_regex'],
		  filters: {'name': frm.doc.country}
		},
		callback: function(r2) {
			let data = r2.message;
			phone_mask = data.custom_dial_code.concat(data.custom_phone_mask);
			// phone_mask = data.phone_mask;
			phone_regix = data.custom_phone_regex;
		}
	  });
}

function apply_mask_on_phones(frm){
	if(phone_mask){
		for(let i=0; i< NoArrays.length; i++){
			frm.fields_dict[NoArrays[i]].$input.mask(phone_mask);
			frm.fields_dict[NoArrays[i]].$input.attr("placeholder", phone_mask);
		}
	}
}

function internationalPhoneValidation(phone, labelName) {
    var pattern = new RegExp(phone_regix);
    if (!(phone.match(pattern)) || phone.length != phone_mask.length) {
		return false;
    } else {
		return true;
    }
}