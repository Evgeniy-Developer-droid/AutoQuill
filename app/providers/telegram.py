import traceback

import httpx
from app.database import async_session_maker
from app.channels import queries as channel_queries
from app.posts import queries as posts_queries
from app.providers.provider import Provider


class Telegram(Provider):

    def __init__(self, post):
        super().__init__(post)
        self.config = post.channel.config_json
        self.base_url = f"https://api.telegram.org/bot{self.config.get('telegram_bot_token')}"

    async def send(self):
        """
        Send the post to the provider.
        """
        async with async_session_maker() as session:
            url = f"{self.base_url}/sendMessage"
            payload = {
                "chat_id": self.config.get("telegram_channel_id"),
                "text": self.post.content,
                "parse_mode": self.config.get("parse_mode", "html"),
            }
            async with httpx.AsyncClient() as client:
                try:
                    response = await client.post(url, json=payload)
                    response.raise_for_status()
                    data = response.json()
                    if data.get("ok"):
                        # Log the successful message
                        await channel_queries.create_channel_log_query({
                            "channel_id": self.post.channel_id,
                            "post_id": self.post.id,
                            "action": "post_send",
                            "message": f"Post sent to Telegram. Message ID: {data['result']['message_id']}"
                        }, session)
                        await posts_queries.update_post_query(self.post.id, {
                            "status": "published"
                        }, session)
                        return data["result"]
                    else:
                        # Log the error message
                        await channel_queries.create_channel_log_query({
                            "channel_id": self.post.channel_id,
                            "post_id": self.post.id,
                            "message": f"Failed to send post to Telegram. Error: {data.get('description')}"
                        }, session)
                        await posts_queries.update_post_query(self.post.id, {
                            "status": "failed"
                        }, session)
                        return None
                except httpx.HTTPStatusError as e:
                    # Log the HTTP error
                    traceback.print_exc()
                    await channel_queries.create_channel_log_query({
                        "channel_id": self.post.channel_id,
                        "post_id": self.post.id,
                        "message": f"HTTP error occurred: {str(e)}"
                    }, session)
                    await posts_queries.update_post_query(self.post.id, {
                        "status": "failed"
                    }, session)
                    return None

