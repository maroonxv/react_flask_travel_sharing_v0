"""
控制台邮件服务实现 (Mock)

仅将邮件内容打印到控制台，用于开发和演示。
"""
from app_auth.domain.demand_interface.i_email_service import IEmailService

class ConsoleEmailService(IEmailService):
    """控制台邮件服务 - Mock实现"""
    
    def send_email(self, to: str, subject: str, content: str) -> None:
        """发送邮件（打印到控制台）"""
        print("\n" + "="*50)
        print(f" [MOCK EMAIL SENT]")
        print(f" 收件人:      {to}")
        print(f" 主题: {subject}")
        print(f" 正文: {content}")
        print("="*50 + "\n")