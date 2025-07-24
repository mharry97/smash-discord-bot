import pytest
from cogs.crossword.getMetro import findMetroPuzzleHTML

@pytest.mark.integration
async def test_live_metro_scraper():
  """
  Checks if the live scraper can connect to the Metro website
  and fetch the expected HTML elements.
  """
  url = "https://metro.co.uk/puzzles/quick-crossword"

  try:
    puzzle_html, across_html, down_html = await findMetroPuzzleHTML(url)

    # Check that we got *some* data back
    assert puzzle_html is not None
    assert across_html is not None
    assert down_html is not None

  except Exception as e:
    pytest.fail(f"Live scraper failed with an exception: {e}")
