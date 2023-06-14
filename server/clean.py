import os
import shutil

def clean():
    """
    Clean the uploads folder and the server.log file
    """
    print("cleaning...")
    if os.path.exists("uploads"):
        shutil.rmtree("uploads")
    os.mkdir("uploads")
    if os.path.exists("server.log"):
        os.remove("server.log")
    print("cleaned")

if __name__ == "__main__":
    clean()
