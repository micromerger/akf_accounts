import frappe
from frappe import _


@frappe.whitelist(allow_guest=True)
def execute(filters=None):
	columns, data = [], []
	if ( filters.get("group_by") == "Supplier"):
		columns = get_columns_for_supplier()
	elif ( filters.get("group_by") == "Account"):
		columns = get_columns_for_account()
	data = get_data(filters)
	return columns, data

def get_columns_for_account():
    columns = [
        _("GL") + ":Data:140",
        _("NTN / CNIC") + ":Data:140",
        _("Branch") + ":Data:140",
        _("Tax Nature") + ":Data:140",
        _("Voucher No") + ":Data:140",
        _("Taxable Amount") + ":Data:140",
        _("Deduction") + ":Data:140",
        _("Deduction Date") + ":Date:140",
        _("WH Tax Rate") + ":Data:140",
        _("Section") + ":Data:140",
        _("Cheque No") + ":Data:140",
        _("Deposit") + ":Data:140",
        _("Deposit Date") + ":Date:140",
        _("CPRN") + ":Data:140",
        _("Default Day(s)") + ":Data:140",
        _("Bill") + ":Data:140",
    ]
    return columns

def get_columns_for_supplier():
    columns = [
        _("NTN / CNIC") + ":Data:140",
        _("GL") + ":Data:140",
        _("Branch") + ":Data:140",
        _("Tax Nature") + ":Data:140",
        _("Voucher No") + ":Data:140",
        _("Taxable Amount") + ":Data:140",
        _("Deduction") + ":Data:140",
        _("Deduction Date") + ":Date:140",
        _("WH Tax Rate") + ":Data:140",
        _("Section") + ":Data:140",
        _("Cheque No") + ":Data:140",
        _("Deposit") + ":Data:140",
        _("Deposit Date") + ":Date:140",
        _("CPRN") + ":Data:140",
        _("Default Day(s)") + ":Data:140",
        _("Bill") + ":Data:140",
    ]
    return columns


def get_data(filters):
	if ( filters.get("group_by") == "Supplier"):
		result = get_query_result_for_supplier(filters)
		structure_result =  get_structure_data(result, "Supplier")
		return structure_result
	elif ( filters.get("group_by") == "Account"):
		result = get_query_result_for_account(filters)
		structure_result =  get_structure_data(result, "Account")
		return structure_result


def get_structure_data(result, group_by):
	structured_data = []
	group_value = group_by
	current_group = None
	Total = {
		"Taxable Amount": 0,
		"Deduction": 0,
		"Deposit": 0,
	}

	for row in result:
		group_value = row[0] 

		if group_value != current_group:
			if current_group is not None:
				structured_data.append([
					"Total for " + current_group, "", "", "", "", 
					Total["Taxable Amount"], 
					Total["Deduction"], "", "", "", "", 
					Total["Deposit"], "", "", "", ""
				])
							
			Total = {
				"Taxable Amount": 0,
				"Deduction": 0,
				"Deposit": 0,
			}

			structured_data.append([_(f"{group_by}: {group_value}"), "", "", "", "", "", "", "", "", "", "", "", "", "", "", ""])
			current_group = group_value

		Total["Taxable Amount"] += row[5] or 0
		Total["Deduction"] += row[6] or 0
		Total["Deposit"] += row[11] or 0

		structured_data.append(list(row))

	if current_group:
		structured_data.append([
			"Total for " + current_group, "", "", "", "", 
			Total["Taxable Amount"], 
			Total["Deduction"], "", "", "", "", 
			Total["Deposit"], "", "", "", ""
		])

	return structured_data

def get_conditions(filters):
    conditions = ""

    if filters.get("company"):
        conditions += " AND gle.company = %(company)s"
    if filters.get("branch"):
        conditions += " AND gle.cost_center = %(branch)s"
    if filters.get("account"):
        conditions += " AND gle.account = %(account)s"

    return conditions


def get_query_result_for_supplier(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
            SELECT 
                gle.party, 
                gle.account, 
                gle.cost_center, 
                atc.charge_type, 
                gle.voucher_no,
                pe.paid_amount,
                atc.tax_amount,
                gle.posting_date, 
                atc.rate, 
                pe.tax_withholding_category, 
                pe.reference_no, 
                atc.tax_amount, 
                pe.custom_deposit_date, 
                atc.custom_cprn, 
                'Default Day(s)', 
                'Bill'
            FROM 
                `tabGL Entry` AS gle
            LEFT JOIN 
                `tabPayment Entry` AS pe
                ON gle.voucher_no = pe.name
            LEFT JOIN 
                `tabAdvance Taxes and Charges` AS atc 
                ON pe.name = atc.parent
            WHERE
                gle.voucher_type = 'Payment Entry' 
                AND gle.party_type = 'Supplier'
                AND pe.apply_tax_withholding_amount = 1
                AND gle.is_cancelled = 0
                {0}
            ORDER BY
				gle.party, gle.account
            """.format(conditions if conditions else ""), filters, as_dict=0,)
    return result

def get_query_result_for_account(filters):
    conditions = get_conditions(filters)
    result = frappe.db.sql(
        """
            SELECT 
                gle.account, 
                gle.party, 
                gle.cost_center, 
                atc.charge_type, 
                gle.voucher_no,
                pe.paid_amount,
                atc.tax_amount,
                gle.posting_date, 
                atc.rate, 
                pe.tax_withholding_category, 
                pe.reference_no, 
                atc.tax_amount, 
                pe.custom_deposit_date, 
                atc.custom_cprn, 
                'Default Day(s)', 
                'Bill'
            FROM 
                `tabGL Entry` AS gle
            LEFT JOIN 
                `tabPayment Entry` AS pe
                ON gle.voucher_no = pe.name
            LEFT JOIN 
                `tabAdvance Taxes and Charges` AS atc 
                ON pe.name = atc.parent
            WHERE
                gle.voucher_type = 'Payment Entry' 
                AND gle.party_type = 'Supplier'
                AND pe.apply_tax_withholding_amount = 1
                AND gle.is_cancelled = 0
                {0}
            ORDER BY
				gle.party, gle.account
            """.format(conditions if conditions else ""), filters, as_dict=0,)
    return result
