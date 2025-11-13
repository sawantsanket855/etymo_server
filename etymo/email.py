from sib_api_v3_sdk.rest import ApiException
import sib_api_v3_sdk
from django.conf import settings


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

def sendMail(subject,to,html_content):
    send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
        to=to,
        sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "GST Web Portal"},
        subject=subject,
        html_content=html_content
        )
    
    try:
        response = api_instance.send_transac_email(send_smtp_email)
        print("✅ Email sent successfully:", response)
        return True
    except ApiException as e:
        print("❌ Error sending email:", e)
        return False