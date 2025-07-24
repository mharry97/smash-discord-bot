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
  # Convert Python dictionaries to JSON strings for storage
  cells_json = json.dumps(cells_dict)
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

  # Unpack the row and convert JSON strings back to Python dictionaries
  return {
    "thread_id": row[0],
    "status": row[1],
    "width": row[2],
    "height": row[3],
    "cells": json.loads(row[4]),
    "clues": json.loads(row[5])
  }


# Update crossword
def update_puzzle_state(thread_id: int, new_cells: dict, new_clues: dict):
  """Updates the cells and clues JSON for a given puzzle."""
  cells_json = json.dumps(new_cells)
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
