import os
import subprocess
import sys

def main():
    print("Dang chay script tao audio giong doc tieng Anh...")
    ps_script = os.path.join(os.path.dirname(__file__), "generate_audio.ps1")
    cmd = ["powershell", "-ExecutionPolicy", "Bypass", "-File", ps_script]
    try:
        ret = subprocess.run(cmd, check=True)
        print("Tao audio thanh cong!")
    except Exception as e:
        print("Loi khi chay script PowerShell:", e)

if __name__ == "__main__":
    main()
