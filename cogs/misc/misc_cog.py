import random
from discord.commands import slash_command
from discord.ext import commands


class MiscCog(commands.Cog):
  def __init__(self, bot):
    self.bot = bot

  @slash_command(name="8ball", description="Ask the Magic 8-Ball a question.")
  async def eight_ball(self, ctx, question: str):
    responses = [
      "It is certain.", "It is decidedly so.", "Without a doubt.",
      "Yes – definitely.", "You may rely on it.", "As I see it, yes.",
      "Most likely.", "Outlook good.", "Yes.", "Signs point to yes.",
      "Reply hazy, try again.", "Ask again later.", "Better not tell you now.",
      "Cannot predict now.", "Concentrate and ask again.",
      "Don't count on it.", "My reply is no.", "My sources say no.",
      "Outlook not so good.", "Very doubtful."
    ]

    await ctx.respond(
      f"🎱 **Question:** {question}\n"
      f"**Answer:** {random.choice(responses)}"
    )


def setup(bot):
  bot.add_cog(MiscCog(bot))
