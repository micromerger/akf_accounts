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
});


function setQueryDesk(frm){
    frm.set_query("donor_desk", function() {
        let ffilters = frm.doc.department == undefined ? { department: ["!=", undefined] } : { department: frm.doc.department };
        return {
            filters: ffilters
        };
    });
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
