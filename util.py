from mip import BINARY

def binary_and(v1, v2, model):
  out_var = model.add_var(var_type=BINARY)
  model += out_var >= v1 + v2 - 1
  model += out_var <= v1
  model += out_var <= v2
  return out_var

def ilp_abs(variable, type, model):
  x = model.add_var(var_type=type)
  model += x >= variable
  model += x >= -variable
  model += (x + variable == 0) + (x - variable == 0) >= 1
  return x
