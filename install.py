   import subprocess
   import sys
   import os

   def install_dependencies():
       print("Installing dependencies...")
       requirements_path = os.path.join(os.path.dirname(__file__), "requirements.txt")
       try:
           subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", requirements_path])
           print("Dependencies installed successfully.")
       except subprocess.CalledProcessError as e:
           print(f"Error installing dependencies: {e}")
           sys.exit(1)

   if __name__ == "__main__":
       install_dependencies()
