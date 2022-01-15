#!/usr/bin/env python3

import sys
import slet

#
# These brackets are a bit weird, but it's the amount of money in each tax
# bracket bucket, rather than income limits.
#
single_tax_brackets = [
    (0.10,   9875),
    (0.12,  30250), #  40,125
    (0.22,  45400), #  85,525
    (0.24,  77805), # 163,330
    (0.32,  44020), # 207,350
    (0.35, 311050), # 518,400
    (0.37, sys.float_info.max),
]

married_tax_brackets = [
    (0.10,  19750),
    (0.12,  60500), #  80,250
    (0.22,  90800), # 171,050
    (0.24, 155550), # 326,600
    (0.32,  88100), # 414,700
    (0.35, 207350), # 622,050
    (0.37, sys.float_info.max),
]

single_ltcg_brackets = [
    (0.00,   40000),
    (0.15,  401450), # 441,450
    (0.20, sys.float_info.max),
]

married_ltcg_brackets = [
    (0.00,   80000),
    (0.15,  416600), # 496,600
    (0.20, sys.float_info.max),
]

estate_tax_brackets = [
    (0,       0,      0.18),
    (10000,   1800,   0.20),
    (20000,   3800,   0.22),
    (40000,   8200,   0.24),
    (60000,   13000,  0.26),
    (80000,   18200,  0.28),
    (100000,  23800,  0.30),
    (150000,  38800,  0.32),
    (250000,  70800,  0.34),
    (500000,  155800, 0.37),
    (750000,  248300, 0.39),
    (1000000, 345800, 0.40),
]

savers_credit_brackets_married = [
    (0,     0.50),
    (39501, 0.20),
    (43001, 0.10),
    (66000, 0.00),
]

savers_credit_brackets_other = [
    (0,     0.50),
    (19751, 0.20),
    (21501, 0.10),
    (33000, 0.00),
]

def calculate_savers_credit(agi, retirement_contributions, married):
    assert agi >= 0
    bracket = savers_credit_brackets_married if married else savers_credit_brackets_other
    for limit, credit_rate in reversed(bracket):
        if agi >= limit:
            return retirement_contributions * credit_rate

def calculate_estate_taxes(estate):
    assert estate > 0
    deduction = 11700000 # $11.7 million for 2021
    taxable_estate = max(0, estate - deduction)
    if not taxable_estate:
        return 0

    for minimum, base_tax, tax_rate in reversed(estate_tax_brackets):
        if taxable_estate > minimum:
            return base_tax + ((taxable_estate - minimum) * tax_rate)

def calculate_minimum_remaining_taxes_for_heir(value, age):
    total_taxes = 0
    while True:
        try:
            rmd = value/slet.withdrawal_factors[age]
            value -= rmd
            total_taxes += calculate_taxes(rmd, True)
        except KeyError:
            break
        age += 1
    return total_taxes

def get_standard_deduction(married):
    return 24800 if married else 12400

def calculate_taxes(agi, married, ltcg=0, just_ltcg=False, debug=False):
    def debug_print(line):
        if debug:
            print(line)

    assert agi >= 0, f"{agi=:.2f}"
    debug_print("Calculating federal income tax")
    standard_deduction = get_standard_deduction(married)
    income_to_tax = max(agi - standard_deduction, 0)
    income_taxes = 0.0
    brackets = married_tax_brackets if married else single_tax_brackets
    for tax_rate, rate_limit in brackets:
        taxable_income_at_rate = min(income_to_tax, rate_limit)
        taxes_at_rate = tax_rate * taxable_income_at_rate
        debug_print(f"{tax_rate=:.2f} * {taxable_income_at_rate=:10,.2f} = {taxes_at_rate=:10,.2f}")
        income_taxes += taxes_at_rate
        income_to_tax -= taxable_income_at_rate
        if income_to_tax == 0:
            break
    debug_print(f"============================================================================")
    debug_print(f"Total: ${income_taxes:,.2f}\n")
    
    debug_print("Calculating long-term capital gains tax")
    income_to_tax = ltcg
    ltcg_taxes = 0
    taxed_income = 0
    brackets = married_ltcg_brackets if married else single_ltcg_brackets
    for tax_rate, rate_limit in brackets:
        if taxed_income < agi:
            taxable_income_at_rate = min((agi - taxed_income), rate_limit)
            debug_print(f"{tax_rate=:.2f} * {taxable_income_at_rate=:10,.2f} = skipping agi")
            taxed_income += taxable_income_at_rate
            rate_limit -= taxable_income_at_rate
            if ((agi - taxed_income) > 0):
                continue
            if not rate_limit:
                continue
            
        taxable_income_at_rate = min(income_to_tax, rate_limit)
        taxes_at_rate = tax_rate * taxable_income_at_rate
        debug_print(f"{tax_rate=:.2f} * {taxable_income_at_rate=:10,.2f} = {taxes_at_rate=:10,.2f}")
        ltcg_taxes += taxes_at_rate
        income_to_tax -= taxable_income_at_rate
        taxed_income += taxable_income_at_rate
        if income_to_tax == 0:
            break
    debug_print(f"============================================================================")
    debug_print(f"Total: ${ltcg_taxes:,.2f}\n")

    if just_ltcg:
        return ltcg_taxes
    else:
        return income_taxes + ltcg_taxes

def fully_tax_deductible_ira(agi, married):
    limit = 104000 if married else 65000
    return agi < limit
