# Smash'D Discord Bot
General bot for the Smash'D frisbee team discord server.

# Current Cogs:
## Crossword Bot
Scrapes today's cryptic crossword from the Metro's website and places it in a thread where users can solve it.
Current state of each crossword is stored in a SQLite table which is upadted
each time the user uses a command.
### Commands
- `/metrocryptic` Command that scrapes the crossword, creates a thread
and then sends the initials state of the crossword and clues. Should be
used on the parent channel instead of in a thread.

- `/answer` The command users use to submit an answer for the crossword by providing the clue and answer.
The updated crossword and clue list will be sent. Should be used on the thread.
  - Example `/answer clue:5d answer:horse`

- `/remove` Removes the inputted clue from the crossword and sends the updated
crossword and clues
  - Example `/remove clue:5d`

## Miscellaneous
A bot for any small commands that don't require their own cog.

### Commands
- `/8ball` Classic fun command that takes a question and responds with 
an answer from a list of possible answers. Should be used on the thread. Is never wrong.
