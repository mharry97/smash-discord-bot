from datetime import datetime

import discord
from discord.ext import commands
import database as db
from cogs.crossword.draw_crossword import drawClues, drawCrossword, getRelevantCells
from cogs.crossword.getMetro import findMetroPuzzleHTML, findCellInfo, getClues, cluesToDic
from PIL import Image
import io

class CrosswordCog(commands.Cog):
    def __init__(self, bot):
        self.bot = bot

    @staticmethod
    def _prepare_image_files(puzzle_image: Image.Image, clues_image: Image.Image) -> list[discord.File]:
      """Converts Pillow Image objects into a list of discord.File objects."""
      files_to_send = []

      # Prepare the puzzle image
      with io.BytesIO() as puzzle_binary:
        puzzle_image.save(puzzle_binary, 'PNG')
        puzzle_binary.seek(0)
        files_to_send.append(discord.File(fp=puzzle_binary, filename="puzzle.png"))

      # Prepare the clues image
      with io.BytesIO() as clues_binary:
        clues_image.save(clues_binary, 'PNG')
        clues_binary.seek(0)
        files_to_send.append(discord.File(fp=clues_binary, filename="clues.png"))

      return files_to_send

    @commands.slash_command(name="metrocryptic",
                            description="Fetch the crossword and create a new thread in the channel")
    async def metrocryptic(self, ctx: discord.ApplicationContext):
      source = "metrocryptic"
      puzzle_date = datetime.now().strftime('%Y-%m-%d')
      channel_id = ctx.channel.id

      existing_thread_id = db.check_puzzle_exists(channel_id, puzzle_date, source)

      if existing_thread_id:
        thread_url = f"https://discord.com/channels/{ctx.guild.id}/{existing_thread_id}"
        await ctx.respond(
          f"Today's Metro Cryptic crossword is already running! You can find it here: {thread_url}",
          ephemeral=True
        )
        return

      await ctx.defer()

      metro_url = "https://metro.co.uk/puzzles/cryptic-crosswords-online-free-daily-word-puzzle/"
      try:
        puzzle_html, across_html, down_html = await findMetroPuzzleHTML(metro_url)
      except Exception as e:
        await ctx.followup.send(f"Error fetching puzzle: {e}", ephemeral=True)
        return

      try:
        cell_dic, grid_width = findCellInfo(puzzle_html)
        down_clues = getClues(down_html, "D")
        across_clues = getClues(across_html, "A")
        all_clues = down_clues + across_clues
        clue_dic = cluesToDic(all_clues, cell_dic)
      except Exception as e:
        await ctx.followup.send(f"Error processing puzzle data: {e}", ephemeral=True)
        return

      puzzle_image_obj = drawCrossword(cell_dic, grid_width)
      clues_image_obj = drawClues(clue_dic)

      try:
        thread = await ctx.channel.create_thread(
          name=f"Metro Cryptic {puzzle_date}",
          type=discord.ChannelType.public_thread,
        )

        db.create_puzzle(
          thread_id=thread.id,
          channel_id=channel_id,
          puzzle_date=puzzle_date,
          source=source,
          width=grid_width,
          height=grid_width,
          cells_dict=cell_dic,
          clues_dict=clue_dic
        )

        files_to_send = self._prepare_image_files(puzzle_image_obj, clues_image_obj)

        await thread.send(
          content="Here are today's crossword and clues!",
          files=files_to_send
        )

        await ctx.followup.send(
          f"Thread '{thread.name}' created successfully!",
          ephemeral=True
        )
      except Exception as error:
        await ctx.followup.send(f"Error creating thread or sending images: {error}", ephemeral=True)

    @commands.slash_command(name="answer", description="Submit an answer")
    async def answer(self, ctx: discord.ApplicationContext, clue: str, answer: str):
      # Check if the clue exists crosswords table
      if not isinstance(ctx.channel, discord.Thread):
        await ctx.respond("This command can only be used inside a crossword thread.", ephemeral=True)
        return

      await ctx.defer()
      thread_id = ctx.channel.id

      # Fetch the current puzzle state from the database
      puzzle_state = db.get_puzzle_state(thread_id)
      if not puzzle_state:
        await ctx.followup.send("This thread does not seem to contain an active crossword.", ephemeral=True)
        return

      # Convert direction and answer to uppercase
      clue = clue.upper().replace(" ", "")
      answer = answer.upper().replace(" ", "")  # Remove whitespace for multi-word answers

      # Validate clue input
      if len(clue) < 2 or not clue[:-1].isdigit() or clue[-1] not in ["A", "D"]:
        await ctx.respond("Invalid clue format! Use a number followed by 'A' or 'D', e.g., '5D'.", ephemeral=True)
        return

      # Verify if the clue exists in the puzzle
      if clue not in puzzle_state["clues"]:
        await ctx.followup.send(f"Clue {clue} not found in the puzzle.", ephemeral=True)
        return

      # Check if the answer length matches the stored length of the clue
      expected_length = sum(puzzle_state["clues"][clue]["lengths"])
      if len(answer) != expected_length:
        await ctx.followup.send(
          f"Answer length mismatch! Clue {clue} expects {expected_length} letters, but you provided {len(answer)}.",
          ephemeral=True
        )
        return

      # Set clue status to solved
      puzzle_state["clues"][clue]["status"] = "solved"

      # Get the starting cell and relevant cells
      start_cell = puzzle_state["clues"][clue]["start"]
      relevant_cells = getRelevantCells(start_cell, expected_length, clue[-1])

      for (x, y), letter in zip(relevant_cells, answer):
        puzzle_state["cells"][(x, y)]["value"] = letter

        # Save the updated state back to the database
      db.update_puzzle_state(thread_id, puzzle_state["cells"], puzzle_state["clues"])

      # Generate and send the new images
      puzzle_image_obj = drawCrossword(puzzle_state["cells"], puzzle_state["width"])
      clues_image_obj = drawClues(puzzle_state["clues"])
      files_to_send = self._prepare_image_files(puzzle_image_obj, clues_image_obj)

      await ctx.followup.send(
        content=f"{ctx.author.mention} answered '{answer}' for clue '{clue}'!",
        files=files_to_send
      )

      # Check for puzzle completion
      all_filled = all(cell["value"] for cell in puzzle_state["cells"].values() if not cell["blank"])
      if all_filled:
        await ctx.channel.send("Congratulations! The crossword is complete!")
        db.update_puzzle_status(thread_id, "completed")

    @commands.slash_command(
      name="remove",
      description="Removes an answer (will remove any intersecting clues' answers)"
    )
    async def remove(self, ctx: discord.ApplicationContext, clue: str):
      # Check we are in a thread
      if not isinstance(ctx.channel, discord.Thread):
        await ctx.respond("This command can only be used inside a crossword thread.", ephemeral=True)
        return

      await ctx.defer()
      thread_id = ctx.channel.id

      # Fetch the current puzzle state from the database
      puzzle_state = db.get_puzzle_state(thread_id)
      if not puzzle_state or puzzle_state.get("status") != "running":
        await ctx.followup.send("This thread does not contain an active crossword.", ephemeral=True)
        return

      # Convert direction
      clue = clue.upper().replace(" ", "")
      if len(clue) < 2 or not clue[:-1].isdigit() or clue[-1] not in ["A", "D"]:
        await ctx.followup.send("Invalid clue format! Use a number followed by 'A' or 'D'.", ephemeral=True)
        return

      if clue not in puzzle_state["clues"]:
        await ctx.followup.send(f"Clue {clue} not found in the puzzle.", ephemeral=True)
        return

      # 3. Update the puzzle state in memory
      clue_data = puzzle_state["clues"][clue]
      clue_data["status"] = "unsolved"

      expected_length = sum(clue_data["lengths"])
      start_cell = clue_data["start"]
      relevant_cells = getRelevantCells(start_cell, expected_length, clue[-1])

      # Clear the values from the cells for this clue
      for x, y in relevant_cells:
        if (x, y) in puzzle_state["cells"]:
          puzzle_state["cells"][(x, y)]["value"] = ""

      # 4. Save the updated state back to the database
      db.update_puzzle_state(thread_id, puzzle_state["cells"], puzzle_state["clues"])

      # 5. Generate and send the new images
      puzzle_image_obj = drawCrossword(puzzle_state["cells"], puzzle_state["width"])
      clues_image_obj = drawClues(puzzle_state["clues"])
      files_to_send = self._prepare_image_files(puzzle_image_obj, clues_image_obj)

      await ctx.followup.send(
        content=f"{ctx.author.mention} removed the answer for clue '{clue}'!",
        files=files_to_send
      )

def setup(bot):
    bot.add_cog(CrosswordCog(bot))
