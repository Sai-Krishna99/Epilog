import os
import subprocess
import tempfile

class PatchApplier:
    @staticmethod
    def apply_patch(project_root: str, file_path: str, diff_content: str) -> bool:
        """
        Safely applies a unified diff to a local file.
        Returns True if successful, False otherwise.
        """
        full_path = os.path.join(project_root, file_path)
        if not os.path.exists(full_path):
            return False

        # Use the `patch` command if available, or a simple fallback
        # For robustness in a controlled environment, we use a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.diff', delete=False) as tmp:
            tmp.write(diff_content)
            tmp_path = tmp.name

        try:
            # -u for unified, -p1 for strip level (though usually 0 for direct paths)
            # We'll try common flags
            result = subprocess.run(
                ["patch", "-u", full_path, "-i", tmp_path],
                capture_output=True,
                text=True
            )
            
            if result.returncode == 0:
                os.unlink(tmp_path)
                return True
            else:
                # Log error
                print(f"Patch failed: {result.stderr}")
                os.unlink(tmp_path)
                return False
        except Exception as e:
            print(f"Exception applying patch: {str(e)}")
            if os.path.exists(tmp_path):
                os.unlink(tmp_path)
            return False
