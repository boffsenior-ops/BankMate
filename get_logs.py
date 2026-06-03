import subprocess

def get_logs():
    try:
        result = subprocess.run(["docker", "logs", "--tail", "50", "bankmate_backend"], capture_output=True, text=True, check=True)
        print("--- STDOUT ---")
        print(result.stdout)
        print("--- STDERR ---")
        print(result.stderr)
    except subprocess.CalledProcessError as e:
        print("Error getting logs")
        print(e.stderr)

if __name__ == "__main__":
    get_logs()
