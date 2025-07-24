from bs4 import BeautifulSoup
import re
from playwright.async_api import async_playwright

async def findMetroPuzzleHTML(url):
    """
    Finds puzzle data using Playwright.

    Args:
      url (str): url of site to get crossword

  Returns:
      list: Three HTML extracts of the puzzle and each set of clues
    """
    async with async_playwright() as p:
        browser = await p.chromium.launch()
        page = await browser.new_page()
        try:
            await page.goto(url, timeout=60000)

            # Wait for the puzzle grid to be visible to ensure the page has loaded
            await page.locator("#puzzle-grid").wait_for(timeout=30000)

            # Find elements directly on the page
            puzzle_html = await page.locator("#puzzle-grid").inner_html()
            across_html = await page.locator(".clue-list.clue-list-across").inner_html()
            down_html = await page.locator(".clue-list.clue-list-down").inner_html()

            return puzzle_html, across_html, down_html
        finally:
            await browser.close()


def getClues(clues_html, direction):
  """
  Extracts clues from the provided HTML and returns them as a list of tuples.

  Args:
      clues_html (str): HTML containing the clues.
      direction (str): "A" for Across, "D" for Down.

  Returns:
      list: A list of tuples (clue number, clue text, direction).
  """
  if not clues_html:
    print("No HTML provided.")
    return []

  soup = BeautifulSoup(clues_html, "html.parser")
  clues = []

  for li in soup.find_all("li"):
    text = li.find("span").get_text(strip=True)
    value = li.get("value")
    direc = direction

    # Fix lengths written as (1-4) instead of (1,4)
    text = re.sub(r"\((\d+)-(\d+)\)", r"(\1,\2)", text)  # Convert (1-4) → (1,4)

    # Only remove " undefined" if it appears **after the length at the end**
    text = re.sub(r"(\([\d,]+\)) undefined$", r"\1", text)  # Removes " undefined" only if after length

    clues.append((value, text, direc))

  return clues


def findClueStart(cell_array, label):
  """
  Find the starting (x, y) position of a clue based on its label.

  Args:
      cell_array (dict): Dictionary of cells, keyed by (x, y), with cell data as values.
      label (str): The label of the clue to find.

  Returns:
      tuple: (x, y) coordinates of the cell with the matching label, or None if not found.
  """
  for (x, y), cell_data in cell_array.items():
    if cell_data.get("label") == str(label):  # Check if the cell's label matches the clue number
      return x, y
  return None  # Return None if no matching cell is found


def cluesToDic(clues, cell_array):
  """
  Converts a list of clues into a structured dictionary.

  Args:
      clues (list): List of clue tuples (number, text, direction).
      cell_array (dict): Dictionary of crossword cells.

  Returns:
      dict: A dictionary mapping clue references (e.g., "5A") to their metadata.
  """
  clues_dic = {}

  for clue in clues:
    direc = clue[2]  # Direction ("A" or "D")
    value = clue[0]  # Clue number
    text = clue[1]  # Clue text
    ref = value + direc  # Reference, e.g., "5A" or "4D"

    # Debugging: Check the clue format
    print(f"[DEBUG] Processing clue: {clue}")

    # Find the starting position of the clue
    start = findClueStart(cell_array, value)
    if not start:
      print(f"[WARNING] Start not found for clue {ref}. Skipping.")
      continue

    # Extract the clue length(s) from the clue text
    clue_length_match = re.search(r'\(([\d,]+)\)$', text)
    if clue_length_match:
      # Convert the length(s) to a list of integers
      clue_lengths = [int(x) for x in clue_length_match.group(1).split(",")]
    else:
      print(f"[WARNING] Length not found for clue {ref}. Skipping.")
      continue  # Skip this clue if the length is not found

    # Store the clue in the dictionary
    clues_dic[ref] = {
      "start": start,  # Starting position (x, y)
      "lengths": clue_lengths,  # List of lengths for the clue
      "status": "unsolved",  # Clue status
      "direction": direc,  # Clue direction
      "text": text,  # Clue text
      "num": value,  # Clue number
    }

  return clues_dic


def findCellInfo(puzzle_html):
  if not puzzle_html:
    print("No HTML provided.")
    return {}, 0  # Return an empty dictionary and 0 rows if no HTML is provided

  soup = BeautifulSoup(puzzle_html, "html.parser")
  cells = {}
  rows = 0

  # Iterate through rows with enumerate to get the row index
  for row_index, tr in enumerate(soup.find_all("tr")):
    rows += 1
    for column_index, td in enumerate(tr.find_all("td")):
      label = td.find("span", class_="cell-label")
      label_text = label.get_text(strip=True) if label else None
      x = column_index
      y = row_index
      value = ""
      clues = set()  # Use a set to track clues that involve this cell
      blank = "inactive" in td.get("class", "")

      # Use (x, y) as the key and store the cell details in a dictionary
      cells[(x, y)] = {
        "blank": blank,  # Whether the cell is a blank cell
        "label": label_text,  # The cell's label
        "value": value,  # The cell's value (updated later with answers)
        "clues": clues  # Clues associated with this cell
      }

  return cells, rows

