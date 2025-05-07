import re
import sys
from core import generator

def main():
    sys.argv[0] = re.sub(r'(-script\.pyw|\.exe)?$', '', sys.argv[0])
    sys.exit(generator.start(sys.argv[1:], []))

if __name__ == '__main__':
    main()