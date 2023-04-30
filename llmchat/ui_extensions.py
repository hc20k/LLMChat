import discord

class PaginationDropdown(discord.ui.Select):
    def __init__(self, options: list[discord.SelectOption], selected_option_idx=-1, callback=None, on_exception=None, _page=0):
        super().__init__(options=[])

        self._callback = callback
        self._on_exception = on_exception
        self._page = _page
        self._per_page = 23
        self._options = options
        self._selected_option_idx = selected_option_idx

        self.options = self.generate_options()


    def generate_options(self):
        # Calculate the number of pages
        _num_pages = (len(self._options) + self._per_page - 1) // self._per_page

        # calculate the start and end indices for the options on the current page
        start_idx = self._page * self._per_page
        end_idx = min(start_idx + self._per_page, len(self._options))

        # only get the options on the current page
        options_on_page = self._options[start_idx:end_idx]

        select_options = []

        # add "Previous" option if necessary
        if self._page > 0:
            select_options.insert(0, discord.SelectOption(label=f"Page {self._page}", value="previous", emoji=discord.PartialEmoji(name="⏮️")))

        # add the specified options
        for option in options_on_page:
            select_options.append(option)

        # add "Next" option if necessary
        if self._page < _num_pages - 1:
            select_options.append(discord.SelectOption(label=f"Page {self._page + 2}", value="next", emoji=discord.PartialEmoji(name="⏭️")))

        return select_options

    async def callback(self, ctx: discord.Interaction):
        try:
            requested_page = None
            if 'next' in ctx.data["values"]:
                requested_page = self._page+1
            elif 'previous' in ctx.data["values"]:
                requested_page = self._page-1

            if requested_page is not None:
                self._page = requested_page
                self.options = self.generate_options()
                await ctx.response.edit_message(view=self.view)
            else:
                await self._callback(ctx)
        except BaseException as e:
            if self._on_exception:
                self._on_exception(e)
            else:
                raise e
