import argparse
import subprocess


def call(cmd):
    cmd = list(filter(None, cmd))
    print('> %s' % ' '.join(cmd))
    subprocess.check_call(cmd)


def push(args):
    delete = '--delete' if args.delete else ''
    call(['rsync', '-av', delete, 'data/', 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data'])


def pull(args):
    delete = '--delete' if args.delete else ''
    call(['rsync', '-av', delete, 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data/', 'data'])


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    pars = subparsers.add_parser('push')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from remote server.')
    pars.set_defaults(func=push)

    pars = subparsers.add_parser('pull')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from local machine.')
    pars.set_defaults(func=pull)

    args = parser.parse_args()
    args.func(args)
