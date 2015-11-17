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


def runbot(define, run):
    """Automatically sets database to Sqlite file that matches script path.

    Example how script path will be converted to sqlite uri:

        bots/vlkk/vardai.py -> sqlite:///data/vlkk/vardai.db

    """
    path = pathlib.Path('data', *pathlib.Path(sys.argv[0]).with_suffix('.db').parts[1:])
    dburi = 'sqlite:///%s' % path
    return databot.Bot(dburi).main(define, run)
