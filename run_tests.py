import subprocess
import sys

result = subprocess.run(
    [sys.executable, "-m", "pytest", "tests/", "-v", "--tb=short"],
    cwd=r"C:\Users\Sultan Computer\Desktop\KisanAI-OS",
    env={**{"PYTHONPATH": r"C:\Users\Sultan Computer\Desktop\KisanAI-OS"}, **dict(__import__('os').environ)},
    capture_output=True,
    text=True,
    timeout=120000,
)

print("STDOUT:")
print(result.stdout)
print("\nSTDERR:")
print(result.stderr)
print("\nReturn code:", result.returncode)