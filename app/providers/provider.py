from app.posts.models import Post


class Provider:

    def __init__(self, post: Post):
        self.post = post

    async def send(self):
        """
        Send the post to the provider.
        """
        raise NotImplementedError("Subclasses must implement send method")