"""
密码哈希器实现

使用 bcrypt 库实现 IPasswordHasher 接口。
"""
import bcrypt

from app_auth.domain.demand_interface.i_password_hasher import IPasswordHasher
from app_auth.domain.value_objects.user_value_objects import Password, HashedPassword


class PasswordHasherImpl(IPasswordHasher):
    """密码哈希器实现 - 使用 bcrypt 算法"""
    
    def hash(self, password: Password) -> HashedPassword:
        """将明文密码哈希化
        
        Args:
            password: 明文密码
            
        Returns:
            哈希后的密码
        """
        # bcrypt.hashpw 需要 bytes
        pwd_bytes = password.value.encode('utf-8')
        salt = bcrypt.gensalt()
        hashed_bytes = bcrypt.hashpw(pwd_bytes, salt)
        
        # 转换回 string 存储
        return HashedPassword(value=hashed_bytes.decode('utf-8'))
    
    def verify(self, password: Password, hashed: HashedPassword) -> bool:
        """验证密码是否匹配
        
        Args:
            password: 明文密码
            hashed: 哈希后的密码
            
        Returns:
            是否匹配
        """
        pwd_bytes = password.value.encode('utf-8')
        hashed_bytes = hashed.value.encode('utf-8')
        
        return bcrypt.checkpw(pwd_bytes, hashed_bytes)
