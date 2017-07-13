import sys
import databot
import pathlib
import importlib.machinery
import pkg_resources as pres


def get_bot_module(path):
    home_path = pres.resource_filename(pres.Requirement.parse('databot-bots'), 'bots')
    module_path = pathlib.Path(home_path, '%s.py' % path)
    if module_path.exists():
        module_name = path.replace('/', '.').replace('-', '_')
        return importlib.machinery.SourceFileLoader('botlib.bots.%s' % module_name, str(module_path)).load_module()
    else:
        raise ValueError("Path '%s' does not exists." % module_path)


def dburi(path, create=False):
    db_path = pathlib.Path('data', '%s.db' % path)
    if create or db_path.exists():
        return 'sqlite:///data/%s.db' % path
    else:
        raise ValueError("Path '%s' does not exists." % db_path)


def getbot(path):
    db_path = pathlib.Path('data', '%s.db' % path)
    if db_path.exists():
        module = get_bot_module(path)
        dburi = 'sqlite:///data/%s.db' % path
        bot = databot.Bot(dburi)
        if hasattr(module, 'define'):
            module.define(bot)
        return bot
    else:
        raise ValueError("Path '%s' does not exists." % db_path)


def find_data_dir(source):
    pth = pathlib.Path(source).with_suffix('.db')
    parts = []
    for i, part in enumerate(reversed(pth.parts)):
        parts.insert(0, part)
        if pth.parents[i].name == 'bots':
            return pth.parents[i + 1] / 'data' / pathlib.Path(*parts)
    raise RuntimeError("Could not find data dir for %s" % source)


def runbot(pipeline):
    """Automatically sets database to Sqlite file that matches script path.

    Example how script path will be converted to sqlite uri:

        bots/vlkk/vardai.py -> sqlite:///data/vlkk/vardai.db

    """
    dburi = 'sqlite:///%s' % find_data_dir(sys.argv[0])
    return databot.Bot(dburi).main(pipeline)
