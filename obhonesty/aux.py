from typing import Any, Optional
from reflex.vars import NumberVar, var_operation, var_operation_return

@var_operation
def two_decimal_points(value: NumberVar):
  """This function will return the value with two decimal points."""
  return var_operation_return(
    js_expression=f"({value}.toFixed(2))",
    var_type=str,
  )

def safe_float_convert(s: str) -> Optional[float]:
  try:
    return float(s)
  except ValueError:
    return None
  except TypeError:
    return None

def value_or(x: Optional[Any], default: Any) -> Any:
  return x if not x is None else default
