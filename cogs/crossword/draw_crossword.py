from PIL import Image, ImageDraw, ImageFont


def drawCrossword(cells, gridWidth):
  font_path = "Roboto-VariableFont_wdth,wght.ttf"
  cell_size = 40
  width = gridWidth
  height = gridWidth

  img_width = width * cell_size
  img_height = height * cell_size

  image = Image.new("RGB", (img_width, img_height), color="white")
  draw = ImageDraw.Draw(image)

  try:
    small_font = ImageFont.truetype(font_path or "", int(cell_size * 0.3))
    large_font = ImageFont.truetype(font_path or "", int(cell_size * 0.6))
  except:
    small_font = None
    large_font = None

  for (x, y), cell_data in cells.items():
    x1 = x * cell_size
    y1 = y * cell_size
    x2 = x1 + cell_size
    y2 = y1 + cell_size

    if cell_data["blank"]:
      draw.rectangle([x1, y1, x2, y2], fill="black", outline="black")
    else:
      draw.rectangle([x1, y1, x2, y2], fill="white", outline="black")

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

      if cell_data["value"]:
        letter_text = cell_data["value"]
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

  return image


def drawClues(cluesDic):
  font_path = "Roboto-VariableFont_wdth,wght.ttf"
  try:
    font = ImageFont.truetype(font_path, size=20)
  except OSError:
    print("Failed to load custom font. Falling back to default font.")
    font = ImageFont.load_default()

  across_clues = {k: v for k, v in cluesDic.items() if v["direction"] == "A"}
  down_clues = {k: v for k, v in cluesDic.items() if v["direction"] == "D"}

  max_clues = max(len(across_clues), len(down_clues))
  line_height = 30
  margin = 50
  image_width = 1300
  image_height = margin * 2 + max_clues * line_height

  img = Image.new("RGB", (image_width, image_height), color="white")
  draw = ImageDraw.Draw(img)

  title_y = margin
  draw.text((margin, title_y), "Across", fill="black", font=font)
  draw.text((image_width // 2, title_y), "Down", fill="black", font=font)

  y_offset = margin + line_height
  for index, clue_type in enumerate([across_clues, down_clues]):
    x_offset = margin if index == 0 else image_width // 2
    current_y = y_offset
    for ref, clue_data in clue_type.items():
      clue_num = clue_data.get("num", ref)
      clue_text = f"{clue_num}. {clue_data['text']}"

      if clue_data["status"] == "solved":
        draw.text((x_offset, current_y), clue_text, fill="gray", font=font)
        bbox = draw.textbbox((0, 0), clue_text, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        draw.line(
          [(x_offset, current_y + text_height // 2),
           (x_offset + text_width, current_y + text_height // 2)],
          fill="red",
          width=2
        )
      else:
        draw.text((x_offset, current_y), clue_text, fill="black", font=font)

      current_y += line_height

  return img


def getRelevantCells(start, length, direction):
  x_start, y_start = start
  relevant_cells = []

  for i in range(length):
    if direction.upper() == "A":
      relevant_cells.append((x_start + i, y_start))
    elif direction.upper() == "D":
      relevant_cells.append((x_start, y_start + i))
    else:
      raise ValueError("Invalid direction. Use 'A' for across or 'D' for down.")
  return relevant_cells
