import sqlite3
import json

DB_FILE = 'bot_data.db'

# Create database
def setup_database():
  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()
  # Create the crosswords table to store crossword progress
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS crosswords (
            thread_id INTEGER PRIMARY KEY,
            channel_id INTEGER NOT NULL,
            puzzle_date TEXT NOT NULL,
            source TEXT NOT NULL,
            status TEXT NOT NULL,
            width INTEGER NOT NULL,
            height INTEGER NOT NULL,
            cells_json TEXT NOT NULL,
            clues_json TEXT NOT NULL,
            UNIQUE(channel_id, puzzle_date, source)
        )
    """)
  connection.commit()
  connection.close()

# Check if a crossword exists
def check_puzzle_exists(channel_id: int, puzzle: str, source: str):
  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()

  # noinspection PyTypeChecker
  cursor.execute("""
    SELECT
      thread_id
    FROM 
      crosswords
    WHERE
      channel_id = ? AND puzzle_date = ? AND source = ?
    """, (channel_id, puzzle, source))

  # Return either single thread_id or None
  result = cursor.fetchone()

  connection.close()

  if result:
    return result[0]  # Return the thread_id itself
  else:
    return None

# Add new crossword to table
def create_puzzle(thread_id: int, channel_id: str, puzzle_date: str, source: str, width: int, height: int, cells_dict: dict, clues_dict: dict):
  """Inserts a new puzzle record into the database."""
  # Convert sets to lists inside the nested cell data
  for cell_data in cells_dict.values():
    if 'clues' in cell_data and isinstance(cell_data['clues'], set):
      cell_data['clues'] = list(cell_data['clues'])

  # Convert tuple keys to strings for JSON compatibility
  cells_json_compatible = {f"{x},{y}": v for (x, y), v in cells_dict.items()}
  cells_json = json.dumps(cells_json_compatible)

  clues_json = json.dumps(clues_dict)
  status = "running"

  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()
  # noinspection PyTypeChecker
  cursor.execute(
    "INSERT INTO crosswords (thread_id, channel_id, puzzle_date, source, status, width, height, cells_json, clues_json) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
    (thread_id, channel_id, puzzle_date, source, status, width, height, cells_json, clues_json)
  )
  connection.commit()
  connection.close()


# Retrieve a puzzles current state
def get_puzzle_state(thread_id: int):
  """Retrieves a puzzle's state from the database and returns it as a Python dictionary."""
  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()
  # noinspection PyTypeChecker
  cursor.execute("SELECT * FROM crosswords WHERE thread_id = ?", (thread_id,))
  row = cursor.fetchone()
  connection.close()

  if not row:
    return None

    # Load and convert keys from JSON string
  cells_from_db = json.loads(row[7])
  cells_dict = {tuple(map(int, k.split(','))): v for k, v in cells_from_db.items()}

  # Convert lists back to sets inside the nested cell data
  for cell_data in cells_dict.values():
    if 'clues' in cell_data and isinstance(cell_data['clues'], list):
      cell_data['clues'] = set(cell_data['clues'])

  # Unpack the row and build the final state dictionary
  return {
    "thread_id": row[0],
    "channel_id": row[1],
    "puzzle_date": row[2],
    "source": row[3],
    "status": row[4],
    "width": row[5],
    "height": row[6],
    "cells": cells_dict,
    "clues": json.loads(row[8])
  }


# Update crossword
def update_puzzle_state(thread_id: int, new_cells: dict, new_clues: dict):
  """Updates the cells and clues JSON for a given puzzle."""

  # Convert sets to lists inside the nested cell data
  for cell_data in new_cells.values():
    if 'clues' in cell_data and isinstance(cell_data['clues'], set):
      cell_data['clues'] = list(cell_data['clues'])

  # Convert tuple keys to strings for JSON compatibility
  cells_json_compatible = {f"{x},{y}": v for (x, y), v in new_cells.items()}
  cells_json = json.dumps(cells_json_compatible)

  clues_json = json.dumps(new_clues)

  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()
  # noinspection PyTypeChecker
  cursor.execute(
    "UPDATE crosswords SET cells_json = ?, clues_json = ? WHERE thread_id = ?",
    (cells_json, clues_json, thread_id)
  )
  connection.commit()
  connection.close()


# Update puzzle status
def update_puzzle_status(thread_id: int, status: str):
  """Updates the status column for a specific puzzle."""
  connection = sqlite3.connect(DB_FILE)
  cursor = connection.cursor()

  # noinspection PyTypeChecker
  cursor.execute(
    "UPDATE crosswords SET status = ? WHERE thread_id = ?",
    (status, thread_id)
  )

  connection.commit()
  connection.close()
