from PIL import Image, ImageDraw, ImageFont

def drawCrossword(cells, gridWidth):
    out_file = "puzzle.png"
    font_path = "Roboto-VariableFont_wdth,wght.ttf"
    cell_size = 40
    width = gridWidth
    height = gridWidth

    # Total image size
    img_width = width * cell_size
    img_height = height * cell_size

    # Create a new white image
    image = Image.new("RGB", (img_width, img_height), color="white")
    draw = ImageDraw.Draw(image)

    # Load fonts
    try:
        small_font = ImageFont.truetype(font_path or "", int(cell_size * 0.3))
        large_font = ImageFont.truetype(font_path or "", int(cell_size * 0.6))
    except:
        # Fallback to a default PIL font
        small_font = None
        large_font = None

    # Draw each cell
    for (x, y), cell_data in cells.items():
        x1 = x * cell_size
        y1 = y * cell_size
        x2 = x1 + cell_size
        y2 = y1 + cell_size

        # Draw black or white cell background
        if cell_data["blank"]:
            draw.rectangle([x1, y1, x2, y2], fill="black", outline="black")
        else:
            draw.rectangle([x1, y1, x2, y2], fill="white", outline="black")

            # Draw label if present
            if cell_data["label"]:
                label_text = cell_data["label"]
                if small_font:
                    draw.text(
                        (x1 + 2, y1 + 2),
                        label_text,
                        font=small_font,
                        fill="black"
                    )
                else:
                    draw.text((x1 + 2, y1 + 2), label_text, fill="black")

            # Draw letter if present
            if cell_data["value"]:
                letter_text = cell_data["value"]
                # Calculate text width/height to center it
                if large_font:
                    bbox = draw.textbbox((0, 0), letter_text, font=large_font)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
                else:
                    bbox = draw.textbbox((0, 0), letter_text, font=None)
                    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]

                text_x = x1 + (cell_size - w) / 2
                text_y = y1 + (cell_size - h) / 2

                if large_font:
                    draw.text((text_x, text_y), letter_text, font=large_font, fill="black")
                else:
                    draw.text((text_x, text_y), letter_text, fill="black")

    return out_file


def drawClues(cluesDic):
    """
    Generate an image of clues with their statuses (solved/unsolved).
    """
    font_path = "Roboto-VariableFont_wdth,wght.ttf"  # Relative path to the Roboto font
    try:
        font = ImageFont.truetype(font_path, size=20)
    except OSError:
        print("Failed to load custom font. Falling back to default font.")
        font = ImageFont.load_default()

    # Separate across and down clues
    across_clues = {k: v for k, v in cluesDic.items() if v["direction"] == "A"}
    down_clues = {k: v for k, v in cluesDic.items() if v["direction"] == "D"}

    # Calculate image dimensions
    max_clues = max(len(across_clues), len(down_clues))
    line_height = 30  # Height for each line of text
    margin = 50  # Margin around the text
    image_width = 1300  # Fixed width
    image_height = margin * 2 + max_clues * line_height

    # Create the image
    img = Image.new("RGB", (image_width, image_height), color="white")
    draw = ImageDraw.Draw(img)
    out_file = "clues.png"

    # Titles
    title_y = margin
    draw.text((margin, title_y), "Across", fill="black", font=font)
    draw.text((image_width // 2, title_y), "Down", fill="black", font=font)

    # Draw clues
    y_offset = margin + line_height  # Start below the titles
    for index, clue_type in enumerate([across_clues, down_clues]):
        x_offset = margin if index == 0 else image_width // 2  # Across on the left, Down on the right
        for ref, clue_data in clue_type.items():
            # Generate clue text
            clue_num = clue_data.get("num", ref)  # Fallback to the reference if no 'num'
            clue_text = f"{clue_num}. {clue_data['text']}"

            # If solved, draw a line through the clue
            if clue_data["status"] == "solved":
                draw.text((x_offset, y_offset), clue_text, fill="gray", font=font)

                # Calculate text bounding box for line placement
                bbox = draw.textbbox((0, 0), clue_text, font=font)
                text_width = bbox[2] - bbox[0]
                text_height = bbox[3] - bbox[1]

                # Draw red line through text
                draw.line(
                    [(x_offset, y_offset + text_height // 2),
                    (x_offset + text_width, y_offset + text_height // 2)],
                    fill="red",
                    width=2
                )
            else:
                draw.text((x_offset, y_offset), clue_text, fill="black", font=font)

            # Increment line position
            y_offset += line_height

        # Reset y_offset for Down clues
        y_offset = margin + line_height

    return out_file




def getRelevantCells(start, length, direction):
    """
    Calculate the list of relevant cells based on the starting position, length, and direction.

    Args:
        start (tuple): Starting position of the answer (x, y).
        length (int): Length of the answer.
        direction (str): Direction of the answer ("A" for across, "D" for down).

    Returns:
        list: A list of tuples representing the (x, y) coordinates of the affected cells.
    """
    x_start, y_start = start  # Unpack the starting coordinates
    relevant_cells = []

    for i in range(length):
        if direction.upper() == "A":  # Across (Horizontal)
            relevant_cells.append((x_start + i, y_start))  # Increment column (y-axis)
        elif direction.upper() == "D":  # Down (Vertical)
            relevant_cells.append((x_start, y_start + i))  # Increment row (x-axis)
        else:
            raise ValueError("Invalid direction. Use 'A' for across or 'D' for down.")
    return relevant_cells

