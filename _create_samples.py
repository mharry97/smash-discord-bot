import asyncio
import os
from cogs.crossword.getMetro import findMetroPuzzleHTML


async def create_samples():
  """
  Runs the live scraper once and saves the HTML to files.
  """
  # Define the target URL and the directory to save samples
  url = "https://metro.co.uk/puzzles/cryptic-crossword/"
  sample_dir = "tests/samples"
  os.makedirs(sample_dir, exist_ok=True)  # Create directory if it doesn't exist

  print("Fetching live data to create samples...")
  try:
    # Fetch the live HTML data
    puzzle_html, across_html, down_html = await findMetroPuzzleHTML(url)

    # Save each piece of HTML to its own file
    with open(os.path.join(sample_dir, "puzzle_grid.html"), "w") as f:
      f.write(puzzle_html)

    with open(os.path.join(sample_dir, "across_clues.html"), "w") as f:
      f.write(across_html)

    with open(os.path.join(sample_dir, "down_clues.html"), "w") as f:
      f.write(down_html)

    print(f"Successfully created sample files in '{sample_dir}'")

  except Exception as e:
    print(f"An error occurred: {e}")


if __name__ == "__main__":
  asyncio.run(create_samples())
