# To implement:
# - Probably needs refactoring
# - Allow for non-square crosswords
# - Work on clue image (probably something to deal with very long clues)
# - Funny comletion message ("Congratulations! I have no idea how you've done")

import os
import discord
from datetime import datetime
from dotenv import load_dotenv
from cogs.crossword.draw_crossword import (
    drawCrossword,
    drawClues,
    getRelevantCells
)
from cogs.crossword.getMetro import findMetroPuzzleHTML, findCellInfo, getClues, cluesToDic

PUZZLE_DATA = {}

load_dotenv()

bot = discord.Bot()

@bot.event
async def on_ready():
    print(f"Running")

@bot.slash_command(
    name="metrocryptic",
    description="Fetch today's Metro cryptic crossword"
)
async def metrocryptic(ctx: discord.ApplicationContext):
    CHANNEL_ID = ctx.channel.id

    # Check if a crossword is already running
    if CHANNEL_ID in PUZZLE_DATA and PUZZLE_DATA[CHANNEL_ID]['status'] == "running":
        thread_id = PUZZLE_DATA[CHANNEL_ID].get("thread_id")
        if thread_id:
            thread_url = f"https://discord.com/channels/{ctx.guild.id}/{thread_id}"
            await ctx.respond(
                f"A crossword is already running! You can access it here: [Metro Cryptic Thread]({thread_url})",
                ephemeral=True
            )
        else:
            await ctx.respond(
                "A crossword is already running! You can't start a new one until the current one ends.",
                ephemeral=True
            )
        return

    await ctx.defer()  # Defer the response to avoid timeout while processing

    # Scrape / parse puzzle HTML
    METRO_URL = "https://metro.co.uk/puzzles/cryptic-crosswords-online-free-daily-word-puzzle/"
    try:
        puzzle_html, across_html, down_html = await findMetroPuzzleHTML(METRO_URL)
    except Exception as e:
        await ctx.respond(f"Error fetching puzzle: {e}")
        return

    # Extract cell data, convert to black/labels/letters
    try:
        cellDic, gridWidth = findCellInfo(puzzle_html)
        downClues = getClues(down_html, "D")
        acrossClues = getClues(across_html, "A")
        allClues = downClues + acrossClues
        clueDic = cluesToDic(allClues, cellDic)
    except Exception as e:
        await ctx.respond(f"Error processing puzzle data: {e}")
        return

    # Generate clue and crossword images
    try:
        drawClues(clueDic)
        drawCrossword(cellDic, gridWidth)
    except Exception as e:
        await ctx.respond(f"Error generating images: {e}")
        return

    today = datetime.today().strftime('%Y-%m-%d')

    try:
        # Create a thread in the current channel
        thread = await ctx.channel.create_thread(
            name=f"Metro Cryptic {today}",
            type=discord.ChannelType.public_thread,
            auto_archive_duration=60  # Auto-archive after 1 hour of inactivity
        )

        # Update PUZZLE_DATA to include the thread ID
        PUZZLE_DATA[CHANNEL_ID] = {
            "cells": cellDic,
            "width": gridWidth,
            "height": gridWidth,
            "status": "running",
            "clues": clueDic,
            "thread_id": thread.id
        }

        # Send the images in a single message within the thread
        await thread.send(
            content="Here are today's crossword and clues!",
            files=[
                discord.File("clues.png"),
                discord.File("puzzle.png")
            ]
        )

        # Respond to the user confirming the thread creation
        await ctx.respond(
            f"Thread '{thread.name}' created successfully!",
            ephemeral=True
        )
    except Exception as error:
        await ctx.respond(f"Error creating thread or sending images: {error}", ephemeral=True)




@bot.slash_command(
    name="answer",
    description="Submit an answer for a clue (e.g., /answer clue:5d answer:beef)"
)
async def answer(ctx: discord.ApplicationContext, clue: str, answer: str):
    # Convert direction and answer to uppercase
    clue = clue.upper().replace(" ", "")
    answer = answer.upper().replace(" ", "")  # Remove whitespace for multi-word answers

    # Validate clue input
    if len(clue) < 2 or not clue[:-1].isdigit() or clue[-1] not in ["A", "D"]:
        await ctx.respond("Invalid clue format! Use a number followed by 'A' or 'D', e.g., '5D'.", ephemeral=True)
        return

    # Parse the clue
    clue_number = int(clue[:-1])  # Extract the number
    direction = clue[-1]  # Extract the direction ('A' or 'D')

    # Check if the clue exists in PUZZLE_DATA
    CHANNEL_ID = ctx.channel.id if ctx.channel.type != discord.ChannelType.public_thread else ctx.channel.parent_id
    if CHANNEL_ID not in PUZZLE_DATA or "clues" not in PUZZLE_DATA[CHANNEL_ID]:
        await ctx.respond("No puzzle data found for this channel. Start a new puzzle first.", ephemeral=True)
        return

    # Verify if the clue exists in the puzzle
    clue_key = f"{clue_number}{direction}"
    if clue_key not in PUZZLE_DATA[CHANNEL_ID]["clues"]:
        await ctx.respond(f"Clue {clue_key} not found in the puzzle.", ephemeral=True)
        return

    # Check if the answer length matches the stored length of the clue
    rawLengths = PUZZLE_DATA[CHANNEL_ID]["clues"][clue_key]["lengths"]

    if len(rawLengths) == 1:
        storedLength = rawLengths[0]
    else:
        storedLength = sum(rawLengths)
    if len(answer) != storedLength:
        await ctx.respond(
            f"Answer length mismatch! Clue {clue_key} expects {storedLength} letters, "
            f"but your answer has {len(answer)} letters.",
            ephemeral=True
        )
        return

    # Set clue status to solved
    PUZZLE_DATA[CHANNEL_ID]["clues"][clue_key]["status"] = "solved"

    # Get the starting cell and relevant cells
    start_cell = PUZZLE_DATA[CHANNEL_ID]["clues"][clue_key]["start"]
    relevant_cells = getRelevantCells(start_cell, storedLength, direction)

    # Update the relevant cells with the answer
    for (x, y), letter in zip(relevant_cells, answer):
        if (x, y) not in PUZZLE_DATA[CHANNEL_ID]["cells"]:
            continue
        cell_data = PUZZLE_DATA[CHANNEL_ID]["cells"][(x, y)]
        cell_data["value"] = letter
        if "cell_clues" not in cell_data:
            cell_data["cell_clues"] = set()
        cell_data["cell_clues"].add(clue_key)

    # Generate clue and crossword images
    try:
        drawClues(PUZZLE_DATA[CHANNEL_ID]["clues"])
        drawCrossword(PUZZLE_DATA[CHANNEL_ID]["cells"], PUZZLE_DATA[CHANNEL_ID]["width"])
    except Exception as e:
        await ctx.respond(f"Error generating images: {e}")
        return

    # Send the images in a single message within the thread
    await ctx.respond(
        content=f"{ctx.author.mention} said '{answer}' for '{clue_key}'!",
        files=[
            discord.File("clues.png"),
            discord.File("puzzle.png")
        ]
    )

    # Check if all cells are filled
    all_filled = all(
        cell_data.get("value", "").strip()  # Safely handle missing or empty values
        for cell_data in PUZZLE_DATA[CHANNEL_ID]["cells"].values()
    )

    if all_filled:
        # Send the completion message in the current context (thread or channel)
        await ctx.channel.send("Congratulations! Maybe!? I have no idea if you did anything right :)")


@bot.slash_command(
    name="remove",
    description="Removes an answer (will remove any intersecting clues' answers)"
)
async def remove(ctx: discord.ApplicationContext, clue: str):
    # Acknowledge the interaction to avoid timeout
    await ctx.defer()

    # Convert direction
    clue = clue.upper().replace(" ", "")

    # Validate clue input
    if len(clue) < 2 or not clue[:-1].isdigit() or clue[-1] not in ["A", "D"]:
        await ctx.respond("Invalid clue format! Use a number followed by 'A' or 'D', e.g., '5D'.", ephemeral=True)
        return

    try:
        # Parse the clue
        clue_number = int(clue[:-1])
        direction = clue[-1]
        clue_key = f"{clue_number}{direction}"

        # Determine the active channel/thread
        CHANNEL_ID = ctx.channel.id if ctx.channel.type != discord.ChannelType.public_thread else ctx.channel.parent_id

        # Verify if the clue exists in the puzzle
        if CHANNEL_ID not in PUZZLE_DATA or clue_key not in PUZZLE_DATA[CHANNEL_ID]["clues"]:
            await ctx.respond(f"Clue {clue_key} not found in the puzzle.", ephemeral=True)
            return

        # Retrieve clue information
        clue_data = PUZZLE_DATA[CHANNEL_ID]["clues"][clue_key]
        rawLengths = clue_data["lengths"]
        storedLength = sum(rawLengths) if len(rawLengths) > 1 else rawLengths[0]
        start_cell = clue_data["start"]
        relevant_cells = getRelevantCells(start_cell, storedLength, direction)

        # Set clue status to unsolved
        clue_data["status"] = "unsolved"

        # Clear the relevant cells
        for (x, y) in relevant_cells:
            if (x, y) in PUZZLE_DATA[CHANNEL_ID]["cells"]:
                cell_data = PUZZLE_DATA[CHANNEL_ID]["cells"][(x, y)]
                cell_clues = cell_data.get("cell_clues", set())
                cell_clues.discard(clue_key)

                if not cell_clues:
                    cell_data["value"] = ""

        # Regenerate the crossword and clue images
        drawClues(PUZZLE_DATA[CHANNEL_ID]["clues"])
        drawCrossword(PUZZLE_DATA[CHANNEL_ID]["cells"], PUZZLE_DATA[CHANNEL_ID]["width"])

        # Respond with updated images
        await ctx.respond(
            content=f"{ctx.author.mention} removed the answer for '{clue_key}'!",
            files=[
                discord.File("clues.png"),
                discord.File("puzzle.png")
            ]
        )

    except Exception as e:
        await ctx.respond(f"An error occurred while processing your request: {e}", ephemeral=True)


@bot.slash_command(
    name="end",
    description="End the current crossword. Behavior depends on where this is used."
)
async def end_puzzle(ctx: discord.ApplicationContext):
    CHANNEL_ID = ctx.channel.id

    # Check if the context is a thread
    if isinstance(ctx.channel, discord.Thread):
        thread_id = ctx.channel.id

        for channel_id, data in PUZZLE_DATA.items():
            if data.get("thread_id") == thread_id:
                del PUZZLE_DATA[channel_id]
                await ctx.channel.send("This crossword has been ended.")
                await ctx.respond("Crossword ended successfully in this thread.", ephemeral=True)
                return

        active_crossword = next(
            (data for data in PUZZLE_DATA.values() if data["status"] == "running"), None
        )
        if active_crossword:
            active_thread_id = active_crossword["thread_id"]
            thread_url = f"https://discord.com/channels/{ctx.guild.id}/{active_thread_id}"
            await ctx.respond(
                f"This thread does not have an active crossword. The active crossword is here: [Active Crossword Thread]({thread_url})",
                ephemeral=True
            )
        else:
            await ctx.respond("There are no active crosswords in this channel.", ephemeral=True)
        return

    if CHANNEL_ID in PUZZLE_DATA:
        thread_id = PUZZLE_DATA[CHANNEL_ID].get("thread_id")
        if thread_id:
            thread_url = f"https://discord.com/channels/{ctx.guild.id}/{thread_id}"
            thread_channel = await bot.fetch_channel(thread_id)
            await thread_channel.send("This crossword has been ended.")
            del PUZZLE_DATA[CHANNEL_ID]
            await ctx.respond(
                f"The crossword has been ended. See the thread here: [Ended Crossword Thread]({thread_url})"
            )
        else:
            del PUZZLE_DATA[CHANNEL_ID]
            await ctx.respond("The crossword has been ended.")
        return

    active_crossword = next(
        (data for data in PUZZLE_DATA.values() if data["status"] == "running"), None
    )
    if active_crossword:
        active_thread_id = active_crossword["thread_id"]
        thread_url = f"https://discord.com/channels/{ctx.guild.id}/{active_thread_id}"
        await ctx.respond(
            f"There is no active crossword in this channel. The active crossword is here: [Active Crossword Thread]({thread_url})",
            ephemeral=True
        )
    else:
        await ctx.respond(
            "There is no active crossword in this channel.",
            ephemeral=True
        )

@bot.slash_command(
    name="debugclues",
    description="Displays the current clues dictionary for debugging."
)
async def debug_clues(ctx: discord.ApplicationContext):
    CHANNEL_ID = ctx.channel.id if ctx.channel.type != discord.ChannelType.public_thread else ctx.channel.parent_id

    if CHANNEL_ID not in PUZZLE_DATA or "clues" not in PUZZLE_DATA[CHANNEL_ID]:
        await ctx.respond("No puzzle data found for this channel. Start a new puzzle first.", ephemeral=True)
        return

    clues = PUZZLE_DATA[CHANNEL_ID]["clues"]
    clues_str = str(clues)

    print(clues_str)
    await ctx.respond("Clues printed to console.", ephemeral=True)


@bot.slash_command(
    name="debugcells",
    description="Displays the current cells array for debugging."
)
async def debug_cells(ctx: discord.ApplicationContext):
    CHANNEL_ID = ctx.channel.id if ctx.channel.type != discord.ChannelType.public_thread else ctx.channel.parent_id

    if CHANNEL_ID not in PUZZLE_DATA or "cells" not in PUZZLE_DATA[CHANNEL_ID]:
        await ctx.respond("No puzzle data found for this channel. Start a new puzzle first.", ephemeral=True)
        return

    cells = PUZZLE_DATA[CHANNEL_ID]["cells"]
    cells_str = str(cells)

    print(cells_str)
    await ctx.respond("Cells printed to console.", ephemeral=True)


# Run bot, run
bot.run(os.getenv('TOKEN'))
