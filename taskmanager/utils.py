def proportional_reduction(width: int, height: int, max_size: int) -> tuple[int, int]:
    if width <= max_size and height <= max_size:
        return width, height

    larger_side = width if width >= height else height
    proportion = max_size / larger_side
    width = int(round(width * proportion, 0))
    height = int(round(height * proportion, 0))
    return width, height
