from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import PromptTemplate
import json
import smtplib
from google.oauth2 import service_account
from googleapiclient.discovery import build
from langchain_core.tools import tool
import base64
from email.message import EmailMessage
import google.auth

# Thiết lập thông tin xác thực cho API Gmail
SCOPES = ['https://www.googleapis.com/auth/gmail.readonly']
SERVICE_ACCOUNT_FILE = 'path/to/your/service-account-file.json'

def get_gmail_service():
    credentials = service_account.Credentials.from_service_account_file(
        SERVICE_ACCOUNT_FILE, scopes=SCOPES)
    return build('gmail', 'v1', credentials=credentials)

# Hàm để kiểm tra xem email có cần phản hồi không
def assess_email_needs_reply(email_content):
    return "?" in email_content  # Giả sử nếu có dấu hỏi thì cần phản hồi

# Tạo runnable cho việc tạo phản hồi cho email
def create_reply_chain():
    prompt_template = "Generate a reply for the following email: {email_content}"
    prompt = PromptTemplate(
        input_variables=["email_content"], template=prompt_template
    )

    return prompt | llm | StrOutputParser()

# Hàm để lấy email mới
def check_new_emails():
    service = get_gmail_service()
    results = service.users().messages().list(userId='me', labelIds=['INBOX'], q='is:unread').execute()
    messages = results.get('messages', [])
    
    for message in messages:
        msg = service.users().messages().get(userId='me', id=message['id']).execute()
        email_content = msg['snippet']  # Lấy nội dung email
        handle_email(email_content)

# Hàm chính để xử lý email
def handle_email(email_content):
    if assess_email_needs_reply(email_content):
        reply_chain = create_reply_chain()
        reply = reply_chain.invoke({"email_content": email_content})
        create_draft(reply)

# Hàm để tạo bản nháp trong Gmail
def create_draft(to, subject, body):
    """Tạo và chèn một bản nháp email."""
    creds, _ = google.auth.default()
    service = get_gmail_service()

    message = EmailMessage()
    message.set_content(body)
    message["To"] = to
    message["From"] = "your_email@example.com"  # Thay thế bằng email của bạn
    message["Subject"] = subject

    # Mã hóa tin nhắn
    encoded_message = base64.urlsafe_b64encode(message.as_bytes()).decode()
    create_message = {"message": {"raw": encoded_message}}

    draft = service.users().drafts().create(userId="me", body=create_message).execute()
    print(f'Draft id: {draft["id"]}\nDraft message: {draft["message"]}')

# Hàm để tạo một tin nhắn email
def create_message(to, subject, body):
    """Tạo một tin nhắn email."""
    message = f"To: {to}\nSubject: {subject}\n\n{body}"
    return base64.urlsafe_b64encode(message.encode('utf-8')).decode('utf-8')

# Ví dụ sử dụng
if __name__ == "__main__":
    check_new_emails()

@tool
def gmail_tool(query: str) -> str:
    """
    Tool to interact with Gmail API.
    Args:
        query (str): The query string provided by the user.
    Returns:
        str: The response from Gmail API.
    """
    # Logic to interact with Gmail API
    return "Gmail tool response"
