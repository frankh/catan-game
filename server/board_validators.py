def desert_on_coast(board):
  desert_hex = [hx for hx in board.land_hexes if hx.tile == "desert"][0]
  return any(hx.is_sea for hx in desert_hex.adj_hexes)

def no_same_value_adjacent(board):
  for hx in board.land_hexes:
    value = hx.value

    return not any(h.value == value for h in hx.adj_hexes)

def no_red_adjacent(board):
  red_values = [6, 8]
  red_hexes = [hx for hx in board.land_hexes if hx.value in red_values]

  for hx in red_hexes:
    if any(h in red_hexes for h in hx.adj_hexes):
      return False

  return True

def no_double_red_resource(board):
  red_values = [6, 8]
  red_hexes = [hx for hx in board.land_hexes if hx.value in red_values]
  red_tiles = [hx.tile for hx in red_hexes]

  return len(red_tiles) == len(set(red_tiles))

def no_same_value_resource(board):
  hex_types = ['fields', 'forest', 'pasture', 'hills', 'mountains']

  for hex_type in hex_types:
    type_hexes = [hx for hx in board.land_hexes if hx.tile == hex_type]
    hex_values = [hx.value for hx in type_hexes]

    if len(set(hex_values)) != len(hex_values):
      return False

  return True

def no_13_plus_vertex(board):
  return not any(v.probability >= 13 for v in board.vertices)