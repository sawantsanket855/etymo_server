from sib_api_v3_sdk.rest import ApiException
import sib_api_v3_sdk
from django.conf import settings
import base64


configuration = sib_api_v3_sdk.Configuration()
configuration.api_key['api-key'] = settings.BREVO_API_KEY

api_instance = sib_api_v3_sdk.TransactionalEmailsApi(
        sib_api_v3_sdk.ApiClient(configuration)
    )

def sendMail(subject,to,html_content, attachments=None):
    
    try:
        brevo_attachments = []
        if attachments:
            for file in attachments:
                file_path = file["path"]
                filename = file_path.split("/")[-1]

                with open(file_path, "rb") as f:
                    encoded = base64.b64encode(f.read()).decode()

                brevo_attachments.append({
                    "name": filename,
                    "content": encoded
                })
        if(brevo_attachments):
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
            to=to,
            sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "GST Web Portal"},
            subject=subject,
            html_content=html_content)
        
        else:
            send_smtp_email = sib_api_v3_sdk.SendSmtpEmail(
                to=to,
                sender={"email": settings.DEFAULT_FROM_EMAIL, "name": "GST Web Portal"},
                subject=subject,
                html_content=html_content,
                attachment=brevo_attachments)
        response = api_instance.send_transac_email(send_smtp_email)
        print("✅ Email sent successfully:", response)
        return True
    except ApiException as e:
        print("❌ Error sending email:", e)
        return False