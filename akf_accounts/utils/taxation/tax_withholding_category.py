def set_sales_tax_and_province_rate(doc, method=None):
	for d in doc.rates:

		applicable_rate = (d.custom_applicable_rate or 0.0)

		tax_rate_percent = (d.custom_tax_rate_percent or 0.0)

		if(applicable_rate==0 and tax_rate_percent==0):
			return

		else:
			rate = (d.tax_withholding_rate or 0.0)

			if(tax_rate_percent > 0):
				# rate = ((18/100) * (0.2/100)) * 100 = (0.18 * 0.002) * 100 = 0.036		
				if(applicable_rate > 0):
					rate = (applicable_rate/100) * (tax_rate_percent) * 100
				else:
					rate = (tax_rate_percent) * 100
				
			# set value
			d.tax_withholding_rate = rate
