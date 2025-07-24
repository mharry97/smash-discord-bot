# tests/crossword/get_clues_test.py
from cogs.crossword.getMetro import getClues

def test_get_across_clues_from_html():
    with open("tests/samples/across_clues.html", "r") as f:
        across_html = f.read()

    # ACROSS CLUES
    actual_clues = getClues(across_html, "A")

    assert len(actual_clues) > 0
    assert actual_clues[0] == ('1', 'Settled little dog, maintaining support (4,2)', 'A') # Test whole of first clue
    assert actual_clues[1][0] == '5' # Check the number of the second clue
    assert actual_clues[2][1] == 'Holding breath let icon physically fit (8)'  # Check the text of the third clue


def test_get_down_clues_from_html():
  with open("tests/samples/down_clues.html", "r") as f:
    down_html = f.read()

  # DOWN CLUES
  actual_clues = getClues(down_html, "D")

  assert len(actual_clues) > 0
  assert actual_clues[0] == ('2', 'Strict writer in tiara again (13)', 'D')  # Test whole of first clue
  assert actual_clues[1][0] == '3'  # Check the number of the second clue
  assert actual_clues[2][1] == 'Fit for drinking by Italian river board (7)'  # Check the text of the third clue
