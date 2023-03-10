import os
import argparse
import src.snapshot_updater as su

def main():
    
    parser = argparse.ArgumentParser(description='Update test snapshots')
    parser.add_argument('--project', '-P', type=str, required=True,
                    help='Absolute path of the project (where go.mod file is located)')
    parser.add_argument('--package', '-pkg', type=str, required=True,
                    help='Absolute path of the package')
    parser.add_argument('--file', '-f', type=str, required=False,
                    help='Absolute path of a test file. If given, only tests belonging to this file will be processed.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)

    args = parser.parse_args()
    projectDir = str(args.project)
    print('Project dir: ', projectDir)

    packageDir = str(args.package)
    print('Package dir: ', packageDir)

    if args.file is None:
        filePath = ''
    else:
        filePath = str(args.file)
    print('File path: ', filePath)

    verbose = bool(args.verbose)
    print('Verbose: ', verbose)

    su.update(projectBaseDir=projectDir, packageDir=packageDir, filePath=filePath, verbose=verbose)


if __name__ == "__main__":
    main()
