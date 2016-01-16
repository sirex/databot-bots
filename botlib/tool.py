import argparse
import subprocess


def call(cmd):
    cmd = list(filter(None, cmd))
    print('> %s' % ' '.join(cmd))
    subprocess.check_call(cmd)


def _rsync(args):
    delete = '--delete-after' if args.delete else ''
    dry_run = '--dry-run' if args.dry_run else ''
    exclude = ['--exclude=%s' % pattern for pattern in [
        '.ipynb_checkpoints/',
        'vtaryba-git/',
    ]]
    return ['rsync', dry_run, '-avi', '--human-readable', '--progress', delete] + exclude


def push(args):
    source = 'data/'
    target = 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data'
    call(_rsync(args) + [source, target])


def pull(args):
    source = 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data/'
    target = 'data'
    call(_rsync(args) + [source, target])


def put(args):
    source = 'data/%s' % args.path
    target = 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data/%s' % args.path
    call(_rsync(args) + [source, target])


def get(args):
    source = 'atviriduomenys.lt:/opt/atviriduomenys.lt/app/var/www/data/%s' % args.path
    target = 'data/%s' % args.path
    call(_rsync(args) + [source, target])


def main():
    parser = argparse.ArgumentParser()

    subparsers = parser.add_subparsers()

    pars = subparsers.add_parser('push')
    pars.add_argument('-n', '--dry-run', action='store_true', default=False,
                      help='Do nothing, just show what would have been transferred.')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from remote server.')
    pars.set_defaults(func=push)

    pars = subparsers.add_parser('pull')
    pars.add_argument('-n', '--dry-run', action='store_true', default=False,
                      help='Do nothing, just show what would have been transferred.')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from local machine.')
    pars.set_defaults(func=pull)

    pars = subparsers.add_parser('put')
    pars.add_argument('path', default='', help='Path on local machine.')
    pars.add_argument('-n', '--dry-run', action='store_true', default=False,
                      help='Do nothing, just show what would have been transferred.')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from remote server.')
    pars.set_defaults(func=put)

    pars = subparsers.add_parser('get')
    pars.add_argument('path', default='', help='Path on remote server.')
    pars.add_argument('-n', '--dry-run', action='store_true', default=False,
                      help='Do nothing, just show what would have been transferred.')
    pars.add_argument('--delete', action='store_true', default=False, help='Delete missing files from local machine.')
    pars.set_defaults(func=get)

    args = parser.parse_args()
    args.func(args)
