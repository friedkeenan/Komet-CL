import discord
from discord.ext import commands
import config
import json
from helpers.checks import check_if_staff
from helpers.userlogs import get_userlog, set_userlog, userlog_event_types


class ModUserlog:
    def __init__(self, bot):
        self.bot = bot

    def get_userlog_embed_for_id(self, uid: str, name: str, own: bool = False,
                                 event=""):
        own_note = " Good for you!" if own else ""
        wanted_events = ["warns", "bans", "kicks", "mutes"]
        if event:
            wanted_events = [event]
        embed = discord.Embed(color=discord.Color.dark_red())
        embed.set_author(name=f"Userlog for {name}")
        userlog = get_userlog()

        if uid not in userlog:
            embed.description = f"There are none!{own_note} (no entry)"
            embed.color = discord.Color.green()
            return embed

        for event_type in wanted_events:
            if event_type in userlog[uid] and userlog[uid][event_type]:
                event_name = userlog_event_types[event_type]
                for idx, event in enumerate(userlog[uid][event_type]):
                    issuer = "" if own else f"Issuer: {event['issuer_name']} "\
                                            f"({event['issuer_id']})\n"
                    embed.add_field(name=f"{event_name} {idx + 1}: "
                                         f"{event['timestamp']}",
                                    value=issuer + f"Reason: {event['reason']}",
                                    inline=False)

        if not own and "watch" in userlog[uid]:
            watch_state = "" if userlog[uid]["watch"] else "NOT "
            embed.set_footer(text=f"User is {watch_state}under watch.")

        if not embed.fields:
            embed.description = f"There are none!{own_note}"
            embed.color = discord.Color.green()
        return embed

    def clear_event_from_id(self, uid: str, event_type):
        userlog = get_userlog()
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        userlog[uid][event_type] = []
        set_userlog(json.dumps(userlog))
        return f"<@{uid}> no longer has any {event_type}!"

    def delete_event_from_id(self, uid: str, idx: int, event_type):
        userlog = get_userlog()
        if uid not in userlog:
            return f"<@{uid}> has no {event_type}!"
        event_count = len(userlog[uid][event_type])
        if not event_count:
            return f"<@{uid}> has no {event_type}!"
        if idx > event_count:
            return "Index is higher than "\
                   f"count ({event_count})!"
        if idx < 1:
            return "Index is below 1!"
        event = userlog[uid][event_type][idx - 1]
        embed = discord.Embed(color=discord.Color.dark_red(),
                              title=f"{event_type} {idx} on "
                                    f"{event['timestamp']}",
                              description=f"Issuer: {event['issuer_name']}\n"
                                          f"Reason: {event['reason']}")
        del userlog[uid][event_type][idx - 1]
        set_userlog(json.dumps(userlog))
        return embed

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(name="userlog",
                      aliases=["listwarns", "getuserlog", "listuserlog"])
    async def userlog_cmd(self, ctx, target: discord.Member):
        """Lists the userlog events for a user, staff only."""
        embed = self.get_userlog_embed_for_id(str(target.id), str(target))
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["listnotes", "usernotes"])
    async def notes(self, ctx, target: discord.Member):
        """Lists the notes for a user, staff only."""
        embed = self.get_userlog_embed_for_id(str(target.id), str(target),
                                              event="notes")
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.command(aliases=["mywarns"])
    async def myuserlog(self, ctx):
        """Lists your userlog events (warns etc)."""
        embed = self.get_userlog_embed_for_id(str(ctx.author.id),
                                              str(ctx.author), True)
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["listwarnsid"])
    async def userlogid(self, ctx, target: int):
        """Lists the userlog events for a user by ID, staff only."""
        embed = self.get_userlog_embed_for_id(str(target), str(target))
        await ctx.send(embed=embed)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarns"])
    async def clearevent(self, ctx, target: discord.Member,
                         event="warns"):
        """Clears all events of given type for a user, staff only."""
        log_channel = self.bot.get_channel(config.log_channel)
        msg = self.clear_event_from_id(str(target.id), event)
        await ctx.send(msg)
        msg = f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"\
              f" all {event} events of {target.mention} | "\
              f"{self.bot.escape_message(target)}"
        await log_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["clearwarnsid"])
    async def cleareventid(self, ctx, target: int, event="warns"):
        """Clears all events of given type for a userid, staff only."""
        log_channel = self.bot.get_channel(config.log_channel)
        msg = self.clear_event_from_id(str(target), event)
        await ctx.send(msg)
        msg = f"🗑 **Cleared {event}**: {ctx.author.mention} cleared"\
              f" all {event} events of <@{target}> "
        await log_channel.send(msg)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarn"])
    async def delevent(self, ctx, target: discord.Member, idx: int,
                       event="warns"):
        """Removes a specific event from a user, staff only."""
        log_channel = self.bot.get_channel(config.log_channel)
        del_event = self.delete_event_from_id(str(target.id), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, discord.Embed):
            await ctx.send(f"{target.mention} has a {event_name} removed!")
            msg = f"🗑 **Deleted {event_name}**: "\
                  f"{ctx.author.mention} removed "\
                  f"{event_name} {idx} from {target.mention} | "\
                  f"{self.bot.escape_message(target)}"
            await log_channel.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)

    @commands.guild_only()
    @commands.check(check_if_staff)
    @commands.command(aliases=["delwarnid"])
    async def deleventid(self, ctx, target: int, idx: int, event="warns"):
        """Removes a specific event from a userid, staff only."""
        log_channel = self.bot.get_channel(config.log_channel)
        del_event = self.delete_event_from_id(str(target), idx, event)
        event_name = userlog_event_types[event].lower()
        # This is hell.
        if isinstance(del_event, discord.Embed):
            await ctx.send(f"<@{target}> has a {event_name} removed!")
            msg = f"🗑 **Deleted {event_name}**: "\
                  f"{ctx.author.mention} removed "\
                  f"{event_name} {idx} from <@{target}> "
            await log_channel.send(msg, embed=del_event)
        else:
            await ctx.send(del_event)


def setup(bot):
    bot.add_cog(ModUserlog(bot))