# tests/crossword/cell_info_test.py
from cogs.crossword.getMetro import findCellInfo

def test_get_across_clues_from_html():
    with open("tests/samples/puzzle_grid.html", "r") as f:
        puzzle_html = f.read()

    #CELL INFO
    cell_dic, grid_width = findCellInfo(puzzle_html)

    assert grid_width == 13 # Check dimensions of grid are correct
    assert len(cell_dic) == grid_width*grid_width # Check every cell has data
    assert cell_dic[(0,0)]["blank"] is False # Check first cell is not blank
    assert cell_dic[(0, 1)]["blank"] is True  # Check blank cell is blank
    assert cell_dic[(1, 0)]["clues"] == set() # Check cell correctly has set initialised

