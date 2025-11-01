import sys
import os

# Add the project root directory to the Python path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

def parse_argu():
    if len(sys.argv) > 1:
        if sys.argv[1] == "1":
            from app.emulator.tmp_01 import run
            run()
        elif sys.argv[1] == "2":
            from app.crawler.tmp_01 import start_point
            start_point()
        elif sys.argv[1] == "3":
            from app.crawler.tmp_02 import start_point
            start_point()
        elif sys.argv[1] == "4":
            from app.emulator.tmp_01 import get_annual_result
            get_annual_result(sys.argv[2], sys.argv[3], sys.argv[4])
    else:
        print("Hello World")

if __name__ == "__main__":
    parse_argu()
