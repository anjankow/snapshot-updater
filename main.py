import sys
import argparse
import snapshots

def main():
    
    parser = argparse.ArgumentParser(description='Update test snapshots')
    parser.add_argument('--projPath', '-P', type=str, required=True,
                    help='Absolute path of the project (where go.mod file is located)')
    parser.add_argument('--packagePath', '-pkg', type=str, required=True,
                    help='Relative path of the package (for example internal/wrapping-package/target-package)')
    parser.add_argument('--file', '-f', type=str, required=False,
                    help='Absolute path of a test file. If given, only tests belonging to this file will be processed.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)

    print(sys.argv)
    args = parser.parse_args()
    print(args)


if __name__ == "__main__":
    main()
