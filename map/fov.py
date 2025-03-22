import numpy as np

def bresenham_line(x0, y0, x1, y1):
    """Bresenham's Line Algorithm - returns a list of points on the line from (x0, y0) to (x1, y1)"""
    dx = abs(x1 - x0)
    dy = abs(y1 - y0)
    sx = 1 if x0 < x1 else -1
    sy = 1 if y0 < y1 else -1
    err = dx - dy
    
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            break
        e2 = 2 * err
        if e2 > -dy:
            err -= dy
            x0 += sx
        if e2 < dx:
            err += dx
            y0 += sy

def calculate_fov(game_map, x, y, radius):
    """Calculate the field of vision from position (x,y) with given radius"""
    # Reset the visible tiles
    game_map.visible = np.full((game_map.height, game_map.width), False, dtype=bool)
    
    # The starting position is always visible
    game_map.visible[y][x] = True
    game_map.explored[y][x] = True
    
    radius_squared = radius * radius
    
    # Cast rays to all tiles within the radius
    for ty in range(max(0, y - radius), min(game_map.height, y + radius + 1)):
        for tx in range(max(0, x - radius), min(game_map.width, x + radius + 1)):
            dx, dy = tx - x, ty - y
            if dx * dx + dy * dy > radius_squared:
                continue  # Outside the radius
            # Cast a ray to (tx, ty)
            for px, py in bresenham_line(x, y, tx, ty):
                if not (0 <= px < game_map.width and 0 <= py < game_map.height):
                    break
                game_map.visible[py][px] = True
                game_map.explored[py][px] = True
                if game_map.tiles[py][px] == game_map.tiles[py][px].__class__.WALL:
                    break  # Stop the ray at walls
