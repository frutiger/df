from __future__ import print_function
import os
import shutil
import subprocess
import sys
import tempfile

def traverse(nodes, get_dependencies):
    result = nodes
    for node in result:
        parents = get_dependencies(node)
        result = result.union(traverse(parents, get_dependencies))
    return result

def tsort(node, get_dependencies):
    nodes = traverse({node}, get_dependencies)
    tsorted = []
    marks   = {}

    def visit(node):
        if node not in marks:
            marks[node] = 'working'
            for child in get_dependencies(node):
                visit(child)
            marks[node] = 'done'
            tsorted.insert(0, node)
        elif marks[node] == 'done':
            return
        else:
            raise RuntimeError('cyclic graph')

    [visit(n) for n in nodes]
    return tsorted

def get_parents(profile):
    parent = os.path.join(profile, 'parents')
    if os.path.isfile(parent):
        with open(parent) as f:
            return set(line[:-1] for line in f.readlines())
    else:
        return set()

def craft_profile(destination, profile):
    for root, dirs, files in os.walk(profile):
        sep = os.path.sep

        source_path = root
        path        = sep.join(root.split(sep)[1:])
        target_path = os.path.join(destination, path)

        for directory in dirs:
            if directory == '.git':
                continue

            target = os.path.join(target_path, directory)
            if os.path.isfile(target):
                raise RuntimeError('{} is a file already'.format(target))
            elif not os.path.isdir(target):
                #print('mkdir {}'.format(target))
                os.makedirs(target)

        for filename in files:
            if filename == '.git':
                continue

            if path == '' and filename == 'parents':
                continue

            source = os.path.join(source_path, filename)
            target = os.path.join(target_path, filename)
            if os.path.isdir(target):
                raise RuntimeError('{} is a dir already'.format(target))
            else:
                with open(source, 'rb') as source_file, \
                     open(target, 'ab') as target_file:
                    for line in source_file:
                        target_file.write(line)

def init_storage(path):
    if os.path.isdir(path):
        raise RuntimeError('Directory already exists at storage location')

    if os.path.isfile(path):
        raise RuntimeError('File already exists at storage location')

    subprocess.check_call(['git',
                           '--git-dir={}'.format(path),
                           'init',
                           '--bare'])
    empty_tree = subprocess.check_output(['git',
                                          'hash-object',
                                          '-t',
                                          'tree',
                                          '/dev/null'])[:-1]
    genesis = subprocess.check_output(['git',
                                       '--git-dir={}'.format(path),
                                       'commit-tree',
                                       '-m',
                                       'genesis',
                                        empty_tree])[:-1]
    subprocess.check_call(['git',
                           '--git-dir={}'.format(path),
                           'update-ref',
                           'HEAD',
                            genesis])

def main():
    def print_usage():
        print('''usage: {} <command> [<args>]

Commands are:
   init   initialize a storage area in the default location
   craft  craft a profile and commit it to the default location
   apply  apply the HEAD of the storage to the default location
   git    run the args as a git command with the default locations'''\
.format(sys.argv[0]))

    if len(sys.argv) < 2:
        print_usage()
        sys.exit(-1)

    if sys.argv[1] == 'init':
        storage = os.path.expanduser('~/.dotfiles.git')
        init_storage(storage)
    elif sys.argv[1] == 'craft':
        profile = sys.argv[2]

        storage  = os.path.expanduser('~/.dotfiles.git')
        temp_dir = tempfile.mkdtemp()

        for profile in reversed(tsort(profile, get_parents)):
            craft_profile(temp_dir, profile)

        subprocess.check_call(['git',
                               '--git-dir={}'.format(storage),
                               '--work-tree={}'.format(temp_dir),
                               'add',
                               '-A'])
        subprocess.check_call(['git',
                               '--git-dir={}'.format(storage),
                               '--work-tree={}'.format(temp_dir),
                               'commit',
                               '--allow-empty',
                               '-m',
                               'update'])

        shutil.rmtree(temp_dir)
    elif sys.argv[1] == 'apply':
        storage = os.path.expanduser('~/.dotfiles.git')
        home    = os.path.expanduser('~')

        subprocess.check_call(['git',
                               '--git-dir={}'.format(storage),
                               '--work-tree={}'.format(home),
                               'checkout',
                               '-p'])
    elif sys.argv[1] == 'git':
        storage = os.path.expanduser('~/.dotfiles.git')
        home    = os.path.expanduser('~')

        args = ['git', '--git-dir={}'.format(storage),
                       '--work-tree={}'.format(home)] + sys.argv[2:]
        subprocess.check_call(args)
    else:
        print_usage()
        sys.exit(-1)

