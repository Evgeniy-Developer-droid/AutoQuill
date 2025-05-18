from app.celery_tasks import send_email_task


class Mailer:

    @staticmethod
    def success_register_mail(email: str):
        """
        Send a success registration email to the user.
        """
        send_email_task.delay(
            subject="Welcome to our service!",
            emails=[email],
            body="Welcome to our service! We are glad to have you on board. If you have any questions, feel free to reach out to us."
        )