// Copyright (c) 2024, Nabeel Saleem and contributors
// For license information, please see license.txt

frappe.ui.form.on('Program', {
    // onload: function(frm) {
        
    // },
    refresh: function(frm){
        set_queries(frm);
    },
    validate: function(frm) {
        frm.doc.deduction_details.forEach(function(row) {
            if (row.percentage < 0 || row.percentage > 100) {
                frappe.throw('Percentage should be between 0 and 100');
            }
            if (row.min_percent < 0 || row.min_percent > 100) {
                frappe.throw('Minimum Percentage should be between 0 and 100');
            }
            if (row.max_percent < 0 || row.max_percent > 100) {
                frappe.throw('Maximum Percentage should be between 0 and 100');
            }
            if (row.max_percent < row.min_percent) {
                frappe.throw('Maximum Percentage cannot be less than Minimum Percentage');
            }
        });
    }
});


function set_queries(frm){
    frm.set_query('receivable_account', function() {
        return {
            filters: {
                account_type: 'Receivable'
            }
        };
    });
    frm.set_query('fund_class', function() {
        return {
            filters: {
                root_type: 'Equity',
                is_group: 0,
                company:frm.doc.company
            }
        };
    });
    frm.fields_dict['deduction_details'].grid.get_field('project').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                company: row.company
            }
        };
    };
    frm.fields_dict['deduction_details'].grid.get_field('account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                root_type: 'Income',
                is_group: 0,
                company: row.company
            }
        };
    };

    frm.fields_dict['accounts_default'].grid.get_field('receivable_account').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                account_type: 'Receivable',
                is_group: 0,
                company: row.company
            }
        };
    };

    frm.fields_dict['accounts_default'].grid.get_field('fund_class').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                root_type: 'Equity',
                is_group: 0,
                company: row.company
            }
        };
    };

    frm.fields_dict['accounts_default'].grid.get_field('cost_center').get_query = function(doc, cdt, cdn) {
        var row = locals[cdt][cdn];
        return {
            filters: {
                is_group: 0,
                disabled: 0,
                company: row.company
            }
        };
    };
}

