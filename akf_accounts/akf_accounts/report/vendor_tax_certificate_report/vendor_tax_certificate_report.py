# Copyright (c) 2024, Nabeel Saleem and contributors
# For license information, please see license.txt

import frappe
from frappe import _
from frappe.utils import (
	fmt_money
)

@frappe.whitelist(allow_guest=True)
def execute(filters=None):
	columns, data = [], []
	columns = get_columns()
	data = get_data(filters)
	return columns, data


def get_columns():
	columns = [
		_("A") + ":Data:220",
		_("B") + ":Data:220",
		_("C") + ":Data:220",
		_("D") + ":Data:220",
	]
	return columns


def get_data(filters):
	TAXPAYERS = get_suppliers_info(filters)
	PAYMENTS = get_payment_particulars(filters)
	data = []
	for supplier in PAYMENTS:
		if(supplier in TAXPAYERS):
			info = TAXPAYERS[supplier]
			data += [
				[text_bold_underline('Tax Payers Particulars')] + ['' for i in range(3)],
				[get_text_bold('NTN'), get_text_underline(info.ntn), get_text_bold('Tax Payer Status'), get_text_underline(info.tax_payer_status)],
				[get_text_bold('CNIC/Reginc No.'), get_text_underline(info.cnic_reginc_no), '', ''],
				[get_text_bold('Name'), get_text_underline(info.supplier_name), '', ''],
				[get_text_bold('Business Name'), get_text_underline(info.business_name), '', ''],
				[get_text_bold('Tax Payer Address'), get_text_underline(info.tax_payer_address), '', ''],
				[get_text_bold('Tax Payer City'), get_text_underline(info.tax_payer_city), '', ''],
				['' for i in range(4)]
			]
			if(supplier in PAYMENTS):
				payments = PAYMENTS[supplier]
				# frappe.throw()
				data += [
					[text_bold_underline('Payment Particulars')] + ['' for i in range(3)],
					[get_text_bold('Payment Section'), get_text_bold('Taxable Amount'), get_text_bold('Tax Deposit'), get_text_bold('CPR#')]
				]
				sumTaxableAmount = 0.0
				sumTaxDeposit = 0.0
				for p in payments:
					data += [	
						[p.payment_section, fmt_money(p.taxable_amount, currency='PKR'), fmt_money(p.tax_deposit, currency='PKR'), p.cprn]
					]
					sumTaxableAmount += float(p.taxable_amount)
					sumTaxDeposit += float(p.tax_deposit)
				data += [['', text_bold_underline(fmt_money(sumTaxableAmount, currency='PKR')), text_bold_underline(fmt_money(sumTaxDeposit, currency='PKR')), '']]
				data += [['' for i in range(4)]]
		
	return data


def get_conditions(filters):
	conditions = ""

	if filters.get("company"):
	    conditions += " AND company = %(company)s"
	if filters.get("supplier"):
	    conditions += " AND custom_tax_payer_id = %(supplier)s"
	if filters.get("from_date") and filters.get("to_date"):
	    conditions += " AND posting_date between %(from_date)s and %(to_date)s"

	return conditions

def get_suppliers_info(filters):
	conditions = " and name = %(supplier)s" if(filters.get("supplier")) else ""
	data = frappe.db.sql(f'''
		Select 
			name,
			ifnull(tax_id, "") as ntn, 
			(supplier_type) as tax_payer_status,
			ifnull(cnic, "") as cnic_reginc_no,
			concat(name, ':', supplier_name) as supplier_name,		
			ifnull(supplier_name, "") as business_name,
			ifnull(supplier_primary_address, "") as tax_payer_address,
			ifnull(country, "") as tax_payer_city
		From 
			`tabSupplier`
		Where
			docstatus=0
			{conditions}
	''', filters,as_dict=1)
	
	sdict = frappe._dict()
	
	for d in data:
		print(d)
		sdict.update({
			d.name: d
		})
	
	return sdict

# bench --site al-khidmat.com execute akf_accounts.akf_accounts.report.vendor_tax_certificate_report.vendor_tax_certificate_report.get_payment_particulars
def get_payment_particulars(filters):
	data = frappe.db.sql(f'''
		Select 
			(custom_tax_payer_id) as tax_payer_id,
			(custom_tax_withholding_category) as payment_section, 
			(custom_tax_payer_total_amount) as taxable_amount,
			(debit_in_account_currency) as tax_deposit,
			(custom_cprn) as cprn
		From 
			`tabGL Entry`
		Where
			docstatus = 1
			and is_cancelled = 0
			and ifnull(custom_cprn, '')!=''
			and ifnull(custom_tax_payer_id, '')!=''
			and ifnull(custom_tax_withholding_category, '')!=''
			{get_conditions(filters)}
		Order by 
			custom_tax_payer_id, custom_tax_withholding_category, custom_cprn
	''', filters, as_dict=1)
	
	cdict = frappe._dict()
	
	for d in data:
		if(d.tax_payer_id in cdict):
			clist = cdict[d.tax_payer_id]
			clist.append(d)
		else:
			cdict.update({
				d.tax_payer_id: [d]
			})
	
	return cdict

def get_text_underline(text):
    return f'<u>{text}</u>'
def text_bold_underline(text):
    return f'<b><u>{text}</u></b>'

def get_text_bold(text):
    return f'<small><b>{text}</b></small>'