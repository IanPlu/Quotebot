import csv
import logging
import os.path
from pathlib import Path
import random
from redbot.core import commands, data_manager
from redbot.core.utils.chat_formatting import (
    escape
)

logger = logging.getLogger("ipl.ewit")

QUOTES_FILE_NAME = "quotes.csv"


class EWit(commands.Cog):
    """Ye Almighty Quotebot, Eternal Witness of Your Sinful Sayings"""
    def __init__(self):
        super().__init__()

        # Get the path to the local quote csv file
        base_path = str(data_manager.cog_data_path(self)).replace("\\", "/")
        self.quotes_file = base_path + "/" + QUOTES_FILE_NAME

        # Set up the quotes csv file if it doesn't already exist
        Path(self.quotes_file).touch()
        if not os.path.isfile(self.quotes_file):
            with open(self.quotes_file, "w") as new_csv:
                logger.info("Quotes csv file not found. Creating a new one.")
                # Write quote 0 on init, so real quotes start at 1
                self.register_quote("\"Hi mortals, I'm buddy!\" - Buddy, at the dawn of time")
        logger.info("EWit Online")

    @commands.command()
    async def quote(self, ctx, *args):
        """
        Record the horrible things folks say for blackmail or later laughs.

        To get a random quote:
        !quote

        To get a quote by its ID number:
        !quote 37

        To record a new quote:
        !quote "You know what they say, hide in plain sight if you like Christmas" - Louis
        Make sure to format your quote correctly so it sorts for ~enhanced features~:
        !quote "<quote body>" - <source>, <optional comment...>
        """
        # *args will be a list of:
        # 1. Entire strings in double quotes
        # 2. and/or whitespace separated single words

        # Parse the args
        if len(args) == 0:
            # Give a random quote
            await ctx.send(self.get_random_quote())
        else:
            if isinstance(args[0], int) or (isinstance(args[0], str) and args[0].isdigit()):
                # Give a quote by the id number provided
                await ctx.send(self.get_quote(int(args[0])))
            else:
                await ctx.send(self.register_quote(args))

    # TODO
    # - Pagination?
    # - Send the file?
    # - Upload somewhere / put in pastebin?
    async def list(self, ctx, *args):
        pass

    # TODO
    # Get a list of quotes that meet some filter criteria
    # Topic -- just a search of the body
    # Author -- all quotes from that author
    # Range -- all quotes from x --> y
    async def find(self, ctx, *args):
        pass

    ### Subcommands ###
    def get_random_quote(self):
        return self.get_quote(random.randint(1, self.__get_num_rows__() - 1))

    # TODO
    # Return a better message on errors-- catch the exception thrown by __read_row__
    # Update formatting so it prints nicely
    # Have it optionally send to a specific channel, so you build a running log of all quotes in THAT channel
    def get_quote(self, number):
        quote = self.__read_row__(number)

        # Split out the quote for better printing
        chunks = list(filter(None, quote.split('|')))

        if len(chunks) == 3:
            return "\"" + chunks[0] + "\" - " + chunks[1] + ", " + chunks[2]
        elif len(chunks) == 2:
            return "\"" + chunks[0] + "\" - " + chunks[1]
        elif len(chunks) == 1:
            return "\"" + chunks[0] + "\""
        else:
            logger.error("Got an empty quote at #" + number)
            return ""

    # TODO:
    # Add Will exception-- if the syntax is irreparably weird, just store the whole thing as the body
    # Better response message-- show the parsed author, return the quote number
    # TODO: Only skip over text[1] if it's a dash or other delimiter
    def register_quote(self, text):
        try:
            # Expecting format: [ "The entire quote body", "-" "Source,", "any", "extra", "comment" ]
            quote_body = text[0]
            quote_source = ""
            quote_comment = ""

            if len(text) > 2:
                # Join together the source + any of the comment
                remainder = " ".join(text[2:])

                # Then split it along the comma, if any
                remainder = remainder.split(", ")

                if len(remainder) > 1:
                    quote_source = remainder[0]
                    quote_comment = ", ".join(remainder[1:])
                else:
                    quote_source = remainder[0]

            self.__write_row__(quote_body, quote_source, quote_comment)

            return "Quote added!"
        except Exception as e:
            logger.error("Failed to register quote", e)
            return "Couldn't add that quote, sorry. Check your formatting and try again."

    ### Util methods ###
    def __write_row__(self, body, source, comment):
        with open(self.quotes_file, "a", newline='') as csvfile:
            writer = csv.writer(csvfile, delimiter='|')
            writer.writerow([ body, source, comment ])
            logger.debug("Wrote row: [ " + " ".join([ body, source, comment ]) + " ]")
            return True

    def __read_row__(self, rownum):
        with open(self.quotes_file, "r", newline='') as csvfile:
            reader = csv.reader(csvfile, delimiter='|')
            rows = [row for row in csvfile]

            if rownum < len(rows):
                logger.debug("Got row: [ " + " ".join(rows[rownum]) + " ]")
                return rows[rownum].rstrip("\r\n")
            else:
                raise Exception("No quote with that number exists")

    def __get_num_rows__(self):
        with open(self.quotes_file, "r", newline='') as csvfile:
            return sum(1 for row in csvfile)

