from __future__ import print_function
import os
import shutil
import subprocess
import sys
import tempfile

class CyclicGraphError(RuntimeError):
    def __init__(self, cycle):
        self.cycle = cycle

def tsort(nodes, adjacencies, normalize=lambda x: x):
    visited   = set()
    postorder = []

    def dft(node, stack):
        if node in visited:
            return

        if node in stack:
            raise CyclicGraphError(list(stack) + [node])

        stack.append(node)
        for adjacent in normalize(adjacencies(node)):
            dft(adjacent, stack)
        stack.pop()

        visited.add(node)
        postorder.insert(0, node)

    for node in normalize(nodes):
        dft(node, [])

    return postorder

def get_parents(profile):
    parent = profile + '.parents'
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
                os.makedirs(target)

        for filename in files:
            if filename == '.git':
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

def main():
    def print_usage():
        print('''usage: {} <command> [<args>]

Commands are:
   init   initialize a storage area in the default location
   craft  craft a profile and commit it to the default location
   apply  apply the HEAD of the storage to the default location
   git    run the args as a git command with the default locations
   graph  produce a graph of the profiles in 'dot' format'''\
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

        profiles = tsort([profile], get_parents, sorted)
        for p in reversed(profiles):
            craft_profile(temp_dir, p)
        for p in profiles:
            end_profile = f'{p}.end'
            if os.path.exists(end_profile):
                craft_profile(temp_dir, end_profile)

        subprocess.check_call(['git',
                               '--git-dir={}'.format(storage),
                               '--work-tree={}'.format(temp_dir),
                               'add',
                               '-A'])
        subprocess.check_call(['git',
                               '--git-dir={}'.format(storage),
                               '--work-tree={}'.format(temp_dir),
                               '-c', 'user.name=stratum',
                               '-c', 'user.email=stratum@localhost',
                               'commit',
                               '--allow-empty',
                               '-m',
                               'crafted from ' + profile])

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
    elif sys.argv[1] == 'graph':
        print('digraph Profiles {')

        for profile in os.listdir('.'):
            if not os.path.isdir(profile):
                continue

            if profile.startswith('.'):
                continue

            if profile.endswith('.end'):
                continue

            print(f'  "{profile}"')
            for parent in get_parents(profile):
                print(f'  "{profile}" -> "{parent}"')

        print('}')
    else:
        print_usage()
        sys.exit(-1)

