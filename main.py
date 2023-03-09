import os
import argparse
import snapshots.snapshot_updater as su

def main():
    
    parser = argparse.ArgumentParser(description='Update test snapshots')
    parser.add_argument('--projPath', '-P', type=str, required=True,
                    help='Absolute path of the project (where go.mod file is located)')
    parser.add_argument('--packagePath', '-pkg', type=str, required=True,
                    help='Absolute path of the package')
    parser.add_argument('--file', '-f', type=str, required=False,
                    help='Absolute path of a test file. If given, only tests belonging to this file will be processed.')
    parser.add_argument('--verbose', '-v', action='store_true', default=False)

    args = parser.parse_args()
    projectPath = str(args.projPath)
    filePath = str(args.file)
    if filePath is None:
        filePath = ''
    # update function expects relative package path,
    # we will subtract the project base path from it
    absolutePkgPath = str(args.packagePath)
    relativePkgPath = absolutePkgPath.replace(projectPath, '')

    if not os.path.isdir(projectPath):
        print('Project directory doesn\'t exist or is invalid: ', projectPath)
        exit(1)

    if not os.path.isdir(absolutePkgPath):
        print('Package directory doesn\'t exist or is invalid: ', absolutePkgPath)
        exit(1)

    if filePath != '':
        if not os.path.isfile(filePath):
            print('File doesn\'t exist: ', filePath)
            exit(1)
        if not filePath.endswith('_test.go'):
            print('File is not a go test file: ', filePath)
            exit(1)

    su.update(projectBasePath=projectPath, packageRelPath=relativePkgPath, filePath=args.file, verbose=args.verbose)


if __name__ == "__main__":
    main()
