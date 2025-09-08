from decimal import Decimal, ROUND_HALF_UP, getcontext
getcontext().prec = 28
def dap_from_rad(rad: float, mpir_percent: float) -> float:
    RAD = Decimal(str(rad)); MPIR = Decimal(str(mpir_percent)) / Decimal('100')
    per_day = (RAD * MPIR) / Decimal('365')
    cents = per_day.quantize(Decimal('0.01'), rounding=ROUND_HALF_UP)
    return float(cents)
