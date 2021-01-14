import tweepy

def checkreplychain(status: tweepy.Status, api: tweepy.API):
    """Checks if the original tweet in a reply chain was from the bot. Returns true if it wasn't."""
    if not status.in_reply_to_status_id:
        if status.user.screen_name == "KosuzuBot":
            print("Original post was from us. Not replying.")
            return False
        else:
            print("We are not the original poster.")
            return True
    else:
        print(f'Tweet was in response to: @{api.get_user(status.in_reply_to_user_id).screen_name}')
        return checkreplychain(api.get_status(status.in_reply_to_status_id), api)
