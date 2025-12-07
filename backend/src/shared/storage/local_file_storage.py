"""
本地文件存储服务

简单的文件存储实现，将文件保存到本地文件系统。
"""
import os
import uuid
from werkzeug.utils import secure_filename
from typing import BinaryIO

class LocalFileStorageService:
    """本地文件存储服务"""
    
    def __init__(self, upload_folder: str = "static/uploads"):
        """初始化存储服务
        
        Args:
            upload_folder: 上传文件保存的基础目录（相对于后端根目录）
        """
        # 确保基础目录存在
        # 假设当前运行目录是 backend/src，向上两级是 backend
        # 但通常建议配置绝对路径，这里为了简单使用相对路径
        self.base_dir = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        self.upload_folder = os.path.join(self.base_dir, upload_folder)
        
        if not os.path.exists(self.upload_folder):
            os.makedirs(self.upload_folder)
            
    def save(self, file_storage, sub_folder: str = "images") -> str:
        """保存文件
        
        Args:
            file_storage: Flask 的 FileStorage 对象
            sub_folder: 子文件夹名称，用于分类存储
            
        Returns:
            str: 文件的访问 URL（相对路径）
        """
        if not file_storage:
            raise ValueError("No file provided")
            
        # 1. 准备保存目录
        save_dir = os.path.join(self.upload_folder, sub_folder)
        if not os.path.exists(save_dir):
            os.makedirs(save_dir)
            
        # 2. 生成安全的文件名
        original_filename = secure_filename(file_storage.filename)
        # 提取扩展名
        _, ext = os.path.splitext(original_filename)
        # 使用 UUID 生成唯一文件名，防止重名覆盖
        unique_filename = f"{uuid.uuid4().hex}{ext}"
        
        # 3. 保存文件
        file_path = os.path.join(save_dir, unique_filename)
        file_storage.save(file_path)
        
        # 4. 返回访问 URL
        # 注意：这里返回的是相对 URL，前端可以直接访问
        # 例如：/static/uploads/images/xxx.jpg
        return f"/static/uploads/{sub_folder}/{unique_filename}"
