# Imports
import discord
import json
import os
from typing import Union
from discord import option, ApplicationContext
from discord.ext import commands

# Variables
client = discord.Bot()
color = discord.Color.random()

# Check for Databases and Autogenerate them
if not os.path.isdir("db"): os.mkdir("db")
if not os.path.isfile("db/profiles.json"):
    with open("db/profiles.json", 'x', encoding="utf-8") as f: json.dump({}, f)
if not os.path.isfile("db/user_ratings.json"):
    with open("db/user_ratings.json", 'x', encoding="utf-8") as f: json.dump({}, f)

# Load Databases
print("[client/startup] Populating databases...")
with open("db/user_ratings.json", 'r') as f: user_ratings = json.load(f)
with open("config/commands.json", 'r') as f: commands_db = json.load(f)
with open("db/profiles.json", 'r') as f: profile_metadata = json.load(f)

# Pre-initialization Commands
def save() -> int:
    """Dumps the latest cached data of all databases to local storage."""
    with open("db/user_ratings.json", 'w+') as f: json.dump(user_ratings, f, indent=4)
    with open("db/profiles.json", 'w+') as f: json.dump(profile_metadata, f, indent=4)  # TODO: Uncomment this line once full profile metadata support is ready
    return 0

def parse_rating(user_id: Union[int, str]) -> float:
    """Parses all the ratings of a specified user, and returns an aggregated rating as `float`."""
    users_rated = []
    for user in user_ratings[str(user_id)].keys():
        users_rated.append(user)
    total_stars = 0
    number_of_ratings = 0
    for uid in users_rated:
        rating = user_ratings[str(user_id)][uid]
        number_of_ratings += 1
        total_stars += rating
    if number_of_ratings == 0: return 0.0  # Return 0 as user rating if no ratings exist, to prevent ZeroDivisionError.
    aggregated_rating = round(total_stars/number_of_ratings, 1)
    return aggregated_rating

# Events
@client.event
async def on_ready():
    print(f"[client] Discord bot user logged in as {client.user.name}")
    print("[client] Ready to accept commands.")
    print("-------------")

@client.event
async def on_message(ctx):
    """Fired whenever someone sends a new rating in a server."""
    if str(ctx.author.id) not in user_ratings: user_ratings[str(ctx.author.id)] = {}
    if str(ctx.author.id) not in profile_metadata: profile_metadata[str(ctx.author.id)] = {"profile_banner_url": None}
    save()

# Slash Commands
@client.slash_command(
    name="help",
    description="Need some command help?"
)
async def _help(ctx: ApplicationContext):
    """Need some command help?"""
    parsed_desc = ""
    for command in commands_db:
        parsed_desc += f"\n\n**{commands_db[command]['name']}**: {commands_db[command]['description']}\nFormat: /{command}{commands_db[command]['args']}"
    localembed = discord.Embed(
        title="My Commands",
        description=parsed_desc,
        color=color
    )
    await ctx.respond(embed=localembed)

@client.slash_command(
    name="rate",
    description="Rate a user of your choice."
)
@option(name="user", description="The person you want to rate", type=discord.User)
@option(name="rating", description="The rating you want to give to the user", type=str, choices=["1 star", "2 stars", "3 stars", "4 stars", "5 stars"])
async def rate(ctx: ApplicationContext, user: discord.User, rating: str):
    """Rate a user of your choice."""
    if str(ctx.author.id) not in user_ratings: user_ratings[str(ctx.author.id)] = {}
    if rating not in ["1 star", "2 stars", "3 stars", "4 stars", "5 stars"]: return
    if rating == "1 star": rating_int = 1
    elif rating == "2 stars": rating_int = 2
    elif rating == "3 stars": rating_int = 3
    elif rating == "4 stars": rating_int = 4
    elif rating == "5 stars": rating_int = 5
    user_ratings[str(user.id)][str(ctx.author.id)] = rating_int
    save()
    localembed = discord.Embed(
        title=":star: Rating Submitted!",
        description=f"You have rated {user.name} {str(rating_int)} {'star' if rating_int == 1 else 'stars'}",
        color=discord.Color.green()
    )
    await ctx.respond(embed=localembed, ephemeral=True)

@client.slash_command(
    name="profile",
    description="View the profile of a user."
)
@option(name="user", description="The user you want to view", type=discord.User, default=None)
async def profile(ctx: ApplicationContext, user: discord.User = None):
    """View the profile of a user."""
    if user == None: user = ctx.author
    localembed = discord.Embed(
        title=f"{user.display_name}'s profile",
        description=f"{user.name}",
        color=discord.Color.random()  # Removed user.accent_color from embed color because PyCord can't behave :(
    )
    localembed.set_thumbnail(url=user.display_avatar)
    localembed.add_field(name="Profile Picture URL", value=f"[Click to view]({user.display_avatar})")
    localembed.add_field(name="Joined Discord at", value=f"{user.created_at.strftime('%d %B, %Y')}")
    localembed.add_field(name="User id", value=user.id)
    localembed.add_field(name="Rating", value=f"{str(parse_rating(user.id))} stars")
    if profile_metadata[str(user.id)]["profile_banner_url"] is not None:
        localembed.set_image(url=profile_metadata[str(user.id)]["profile_banner_url"])
    await ctx.respond(embed=localembed)

@client.slash_command(
    name="rating",
    description="View a user's rating."
)
@option(name="user", description="The user you want to view", type=discord.User, default=None)
async def rating(ctx: ApplicationContext, user: discord.User = None):
    """View a user's rating."""
    if user == None: user = ctx.author
    localembed = discord.Embed(
        description=f":star: {user.name} has been rated {str(parse_rating(user.id))} stars",
        color=color
    )
    await ctx.respond(embed=localembed)

# User Profile Customization Commands
customization = client.slash_group("customize", "Commands used to customize the user's /profile command.")

@customization.command(
    name="profile_banner",
    description="Set a banner to display on your /profile command! (url only)"
)
@option(name="image_url", description="The url of your new profile banner (leave blank to disable)", type=str, default=None)
async def banner(ctx: ApplicationContext, image_url: str = None):
    """Set a banner to display on your /profile command! (url only)"""
    if (image_url is not None) and ("https://" not in image_url):
        return await ctx.respond("Your custom banner url must contain `https://`!", ephemeral=True)
    profile_metadata[str(ctx.author.id)]["profile_banner_url"] = image_url
    if image_url is None: localembed = discord.Embed(description=":white_check_mark: Your custom profile banner has been successfully removed.", color=discord.Color.green())
    else: localembed = discord.Embed(description=":white_check_mark: Your custom profile banner has been successfully set! Check it out using `/profile`.", color=discord.Color.green())
    return await ctx.respond(embed=localembed)

# User Commands
@client.user_command(name="View Profile")
async def _profile(ctx: ApplicationContext, user: discord.User):
    await profile(ctx, user)

@client.user_command(name="View Rating")
async def _rating(ctx: ApplicationContext, user: discord.User):
    await rating(ctx, user)

# Bot Initialization
try:
    with open("config/auth.json", 'r', encoding="utf-8") as f: auth_config = json.load(f)
    if auth_config["deploy_mode"] == "replit": client.run(os.getenv["TOKEN"])
    if auth_config["deploy_mode"] == "local":
        if auth_config["TOKEN"] == "": 
            print("Unable to deploy client: You have not added a bot token yet. Add one first in 'TOKEN' in 'config/auth.json'.")
            print("You can get a bot token from https://discord.com/developers by creating a new application.")
            raise SystemExit
        print("[main/Startup] Initializing bot client...")
        client.run(auth_config["TOKEN"])
except KeyError:
    print("Unable to deploy client: Your configuration file is likely corrupted. Please reinstall the bot.")
    raise SystemExit
except Exception as error:
    print(f"An error occured when trying to deploy the client.\nError Info:\n   {type(error).__name__}\n   {error}")
    raise SystemExit
