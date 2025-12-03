import sys
import os

print("Current working directory:", os.getcwd())
print("Script path:", __file__)

src_path = os.path.join(os.path.dirname(__file__), '../src')
print("Adding to sys.path:", os.path.abspath(src_path))
sys.path.append(src_path)

try:
    from app_auth.domain.value_objects.value_objects import UserId
    print("Successfully imported UserId")
except ImportError as e:
    print(f"ImportError: {e}")
except Exception as e:
    print(f"Error: {e}")
