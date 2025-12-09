"""
邮件服务接口

定义发送邮件的抽象能力。
"""
from abc import ABC, abstractmethod

class IEmailService(ABC):
    """邮件服务接口"""
    
    @abstractmethod
    def send_email(self, to: str, subject: str, content: str) -> None:
        """发送邮件
        
        Args:
            to: 收件人邮箱
            subject: 邮件主题
            content: 邮件内容
        """
        pass