
units = {}

units['nfo'] = {'type': 'nfo', 'convert': 1, 'ottd_mul': 1, 'ottd_shift': 0} #don't convert, take value literal

# Conversion factor works like this:
# 1 reference_unit = convert other_unit
# So nfo_value = property_value / convert * property_specific_conversion_factor

# ottd_mul and ottd_shift are the values taken from OpenTTD's src/strings.cpp and
# are used to calculate the displayed value by OpenTTD. If possible, adjust_values
# increases or decreases the NFO value so that the desired display value is actually
# achieved

#Speed (reference: m/s)
units['mph'] = {'type': 'speed', 'convert': 2.236936, 'ottd_mul': 1, 'ottd_shift': 0}
units['km/h'] = {'type': 'speed', 'convert': 3.6, 'ottd_mul': 103, 'ottd_shift': 6}
units['m/s'] = {'type': 'speed', 'convert': 1, 'ottd_mul': 1831, 'ottd_shift': 12}

#Power (reference: hpI (imperial hp))
units['hp'] = {'type': 'power', 'convert': 1, 'ottd_mul': 1, 'ottd_shift': 0} # Default to imperial hp
units['kW'] = {'type': 'power', 'convert': 0.745699, 'ottd_mul': 6109, 'ottd_shift': 13}
units['hpM'] = {'type': 'power', 'convert': 1.013869, 'ottd_mul': 4153, 'ottd_shift': 12}
units['hpI'] = {'type': 'power', 'convert': 1, 'ottd_mul': 1, 'ottd_shift': 0}

#Weight (reference: ton)
units['ton'] = {'type': 'weight', 'convert': 1, 'ottd_mul': 1, 'ottd_shift': 0}
units['tons'] = {'type': 'weight', 'convert': 1, 'ottd_mul': 1, 'ottd_shift': 0}
units['kg'] = {'type': 'weight', 'convert': 1000.0, 'ottd_mul': 1000, 'ottd_shift': 0}
