// Copyright (c) 2017, Frappe Technologies Pvt. Ltd. and contributors
// For license information, please see license.txt
// Masks
let cnic = "99999-9999999-9";
let ntn = "999999-9";
let passport = "999999999";
let cnicRegix = /^\d{5}-\d{7}-\d{1}$/;
let ntnRegix = /^\d{6}-\d{1}$/;
let passportRegix = /^\d{9}$/;
// =>

let NoArrays = ['contact_no'];
/* mobile no validation */
var dial_code = null;
var phone_mask = null;
var phone_mask_length = 0;
var phone_regix = null;
var mobileFieldName = null;
/* end.. */

frappe.ui.form.on('Donor', {
    refresh: function (frm) {
        frappe.dynamic_link = { doc: frm.doc, fieldname: 'name', doctype: 'Donor' };

        frm.toggle_display(['address_html', 'contact_html'], !frm.doc.__islocal);

        if (!frm.doc.__islocal) {
            frappe.contacts.render_address_and_contact(frm);
        } else {
            frappe.contacts.clear_address_and_contact(frm);
        }
        set_queries.applying(frm);
        // Nabeel Saleem, 02-01-2025
        get_country_detail(frm);
        apply_mask_on_phones(frm);
        // End
        apply_mask_on_id_number(frm);
        // Nabeel Saleem, 20-01-2025
        btns.applying_btns(frm);

    },
    identification_type: function (frm) {
        if (frm.doc.identification_type != "Others") {
            apply_mask_on_id_number(frm);

        }
        frm.set_value("cnic", "");
        frm.set_value("others", "");
    },
    cnic: function (frm) {
        // console.log(frm.doc.cnic)
        if (frm.doc.cnic && frm.doc.identification_type != "Other") {
            const labelName = __(frm.fields_dict['cnic'].df.label);
            if (!internationalIdNumberValidation(frm.doc.cnic, frm.doc.identification_type)) {
                // frm.set_value('cnic', '');
                frm.set_df_property("cnic", "description", `<p style="color:red">Please enter valid ${labelName}</p>`)
                // frm.set_intro(`Please enter valid ${labelName}`, 'red');
            } else {
                frm.set_df_property("cnic", "description", "")
            }
        } else {
            frm.set_df_property("cnic", "description", "")
        }
    },
    country: function (frm) {
        get_country_detail(frm);
        apply_mask_on_phones(frm);
    },
    contact_no: function (frm) {
        if (frm.doc.contact_no) {
            const labelName = __(frm.fields_dict['contact_no'].df.label);
            if (!internationalPhoneValidation(frm.doc.contact_no, labelName)) {
                frm.set_df_property('contact_no', 'description', `<p style="color:red">Please enter valid ${labelName}</p>`);
            } else {
                frm.set_df_property('contact_no', 'description', "");
            }
        } else {
            frm.set_df_property('contact_no', 'description', "");
        }
    },
    validate: function (frm) {
        if (frm.doc.contact_no) {
            const labelName = __(frm.fields_dict['contact_no'].df.label);
            internationalPhoneValidation(frm.doc.contact_no, labelName);
        }
    },
    default_currency: function (frm) {
        frm.call("validate_default_account");
    }
});


set_queries = {
    applying: function (frm) {
        set_queries.donor_desk_func(frm);
        set_queries.donor_primary_address_func(frm);
        set_queries.donor_primary_contact_func(frm);
        set_queries.default_currency_func(frm);
        set_queries.default_account_func(frm);
    },
    donor_desk_func: function (frm) {
        frm.set_query("donor_desk", function () {
            let ffilters = frm.doc.department == undefined ? { department: ["!=", undefined] } : { department: frm.doc.department };
            return {
                filters: ffilters
            };
        });
    },
    donor_primary_address_func: function (frm) {
        frm.set_query('donor_primary_address', function (doc) {
            return {
                filters: {
                    'link_doctype': 'Donor',
                    'link_name': doc.name
                }
            }
        });
    },
    donor_primary_contact_func: function (frm) {
        frm.set_query('donor_primary_contact', function (doc) {
            return {
                query: "akf_accounts.akf_accounts.doctype.donor.donor.get_donor_primary_contact",
                filters: {
                    'donor': doc.name
                }
            }
        })
    },
    default_currency_func: function (frm) {
        frm.set_query('default_currency', function (doc) {
            return {
                filters: {
                    'enabled': 1
                }
            }
        })
    },
    default_account_func: function (frm) {
        frm.set_query('default_account', function (doc) {
            const currency = frm.doc.default_currency == undefined ? "" : frm.doc.default_currency;
            return {
                filters: {
                    'disabled': 0,
                    'is_group': 0,
                    'account_currency': currency,
                    'account_type': "Receivable",
                }
            }
        })
    },

}

btns = {
    applying_btns: function (frm) {
        if (frm.doc.__islocal) return
        btns.foriegn_donor_func(frm);
        btns.link_with_supplier_func(frm);

    },
    foriegn_donor_func: function (frm) {
        if (frm.doc.is_group == 1 || frm.doc.parent_donor == undefined) {
            frm.add_custom_button(__('Foriegn Donor'), function () {
                dilaoges.show_foriegn_donor_dialog(frm);
            }, __('Create'));
        }
    },
    link_with_supplier_func: function (frm) {
        if (cint(frappe.defaults.get_default("enable_common_party_accounting"))) {
            frm.add_custom_button(__('Link with Supplier'), function () {
                dilaoges.show_party_link_dialog(frm);
            }, __('Create'));
        }
    },
}

function apply_mask_on_id_number(frm) {
    let maskValue = "";
    frm.set_df_property("cnic", "label", frm.doc.identification_type);
    if (frm.doc.identification_type === "CNIC") {
        maskValue = cnic;
    } else if (frm.doc.identification_type === "NTN") {
        maskValue = ntn;
    } else if (frm.doc.identification_type === "Passport") {
        maskValue = passport;
    }

    frm.fields_dict["cnic"].$input.mask(maskValue);
    frm.fields_dict["cnic"].$input.attr("placeholder", maskValue);

}

function internationalIdNumberValidation(cnicNo, identification_type) {
    // var pattern = new RegExp("^\d{5}-\d{7}-\d{1}$");
    let pattern = identification_type == "NTN" ? ntnRegix : (identification_type == "Passport" ? passportRegix : cnicRegix);
    let masking = identification_type == "NTN" ? ntn : (identification_type == "Passport" ? passport : cnic);
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
function get_country_detail(frm) {
    if (!frm.doc.country) return
    frappe.call({
        method: "frappe.client.get_value",
        async: false,
        args: {
            doctype: 'Country',
            fieldname: ['custom_dial_code', 'custom_phone_mask', 'custom_phone_regex'],
            filters: { 'name': frm.doc.country }
        },
        callback: function (r2) {
            let data = r2.message;
            phone_mask = data.custom_dial_code.concat(data.custom_phone_mask);
            // phone_mask = data.phone_mask;
            phone_regix = data.custom_phone_regex;
        }
    });
}

function apply_mask_on_phones(frm) {
    if (phone_mask) {
        for (let i = 0; i < NoArrays.length; i++) {
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


/* 
Common Party Accounting

Link donor with supplier to enable common party accounting.

after that create new donation then there will be a jounal entry auto created against donation.
*/
dilaoges = {
    show_party_link_dialog: function (frm) {
        const dialog = new frappe.ui.Dialog({
            title: __('Select a Supplier'),
            fields: [{
                fieldtype: 'Link', label: __('Supplier'),
                options: 'Supplier', fieldname: 'supplier', reqd: 1
            }],
            primary_action: function ({ supplier }) {
                frappe.call({
                    method: 'erpnext.accounts.doctype.party_link.party_link.create_party_link',
                    args: {
                        primary_role: 'Donor',
                        primary_party: frm.doc.name,
                        secondary_party: supplier
                    },
                    freeze: true,
                    callback: function () {
                        dialog.hide();
                        frappe.msgprint({
                            message: __('Successfully linked to Supplier'),
                            alert: true
                        });
                    },
                    error: function () {
                        dialog.hide();
                        frappe.msgprint({
                            message: __('Linking to Supplier Failed. Please try again.'),
                            title: __('Linking Failed'),
                            indicator: 'red'
                        });
                    }
                });
            },
            primary_action_label: __('Create Link')
        });
        dialog.show();
    },
    show_foriegn_donor_dialog: function (frm) {
        const d = new frappe.ui.Dialog({
            title: __('Foriegn Currency Donor'),
            fields: [
                {
                    label: __('Currency'),
                    fieldtype: 'Link',
                    fieldname: 'default_currency',
                    options: 'Currency',
                    reqd: 1,
                    onchange: function () {
                        let currency = d.fields_dict.default_currency.value;
                        let account = client_api.get_account(currency);
                        d.fields_dict.default_account.value = account;
                        d.fields_dict.default_account.df.description = (account == "") ? "<b style='color:red;'>* Account not found.</b>" : "";
                        d.fields_dict.default_account.refresh();
                    }
                },
                {
                    label: __('Account'),
                    fieldtype: 'Link',
                    fieldname: 'default_account',
                    options: 'Account',
                    reqd: 1,
                    read_only: 1
                },
            ],
            primary_action: function (data) {
                frappe.model.open_mapped_doc({
                    method: "akf_accounts.akf_accounts.doctype.donor.donor.make_foriegn_donor",
                    frm: cur_frm,
                    args: data
                });
            },
            primary_action_label: __('Create')
        });
        d.show();
    }
}


client_api = {
    get_account: function (currency) {
        let account = "";
        if (currency) {
            frappe.call({
                method: "frappe.client.get_value",
                async: false,
                args: {
                    doctype: 'Account',
                    fieldname: ['name'],
                    filters: { 'disabled': 0, "is_group": 0, "account_type": "Receivable", "account_currency": currency }
                },
                callback: function (r) {
                    let data = r.message;
                    console.log(data);
                    if ("name" in data) {
                        account = data.name;
                    }
                }
            });
        }
        return account
    }
}