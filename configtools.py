import os
import os.path

import configparser
import textwrap

CONFIG_FILE_NAME = ".remoterun"

DEFAULT_CONFIG_TEXT = textwrap.dedent('''
    # This is an initial remote run config
    # Set following options:

    # Url of host to sync
    RemoteHost = example.com

    # Path on the remote host to sync with
    RemoteDir = /home/foo/rr/
        
    # You can also select some optional arguments

    # Receive or not if remote command failed (yes/no/ask)
    # ReceiveIfFailed = ask

    # Add command(s) or prefix before each command
    # BeforeExec = . .profile;

    # LogLevel = info

    [rsync]

    # General filters for rsync, newline-separated (indent line with values)
    # See 'man rsync' or https://man.developpez.com/man1/rsync/#L15
    # Filters =
    #   + /foo/**
    #   - bar
    
    # List of subdirs to sync, newline-separated (indent line with values)
    # Mix 'SelectDirs' and 'Filters' carefully
    #SelectDirs = 
    #   foo/bar
    #   foo/baz/bar
    #   bar

    ''').strip()

DEFAULTS = {
    'ReceiveIfFailed': 'ask',
    'LogLevel': 'info',
    'BeforeExec':'',
    'Filters':'',
    'SelectDirs':'', 
    }


def find_config(directory):
    while True:
        config_file = os.path.join(directory, CONFIG_FILE_NAME)
        if os.path.exists(config_file):
            return config_file

        directory, splitted = os.path.split(directory)
        if not splitted:
            raise RuntimeError("RemoteRun not configured for this directory")


def _to_log_level(level):
    level = level.upper()
    if level not in {'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'}:
        raise RuntimeError('Unknown logging level: {}'.format(level))
    else:
        return level


def parse_config(config_file):
    with open(config_file) as f:
        config_text = f.read()

    if config_text.find('[main]') == -1:
        config_text = '[main]\n' + config_text # Add placeholder section

    config_parser = configparser.ConfigParser(
        defaults=DEFAULTS, empty_lines_in_values=True)
    config_parser.read_string(config_text)

    return {
        'remote_host': config_parser['main']['RemoteHost'],
        'remote_root': config_parser['main']['RemoteDir'],
        'before_exec': config_parser['main']['BeforeExec'],
        'receive_if_failed': config_parser['main']['ReceiveIfFailed'],
        'log_level': _to_log_level(config_parser['main']['LogLevel']),
        'rsync' : {
                'filters': config_parser.get('rsync','Filters'),
                'select_dirs': config_parser.get('rsync','SelectDirs'),
            }
        }


def get_settings():
    local_dir = os.path.realpath(os.curdir)
    config_file = find_config(local_dir)
    local_root = os.path.dirname(config_file)

    settings = {
        'local_dir': local_dir,
        'local_root': local_root,
        'rel_path': os.path.relpath(local_dir, local_root)
        }

    settings.update(parse_config(config_file))
    settings['remote_dir'] = os.path.normpath(os.path.join(settings['remote_root'], settings['rel_path']))

    return settings


def create_initial_config():
    if os.path.exists(CONFIG_FILE_NAME):
        raise RuntimeError('Config is already saved in {}'.format(CONFIG_FILE_NAME))

    with open(CONFIG_FILE_NAME, mode='w') as config_file:
        print(DEFAULT_CONFIG_TEXT, file=config_file)

    os.system('vim {}'.format(CONFIG_FILE_NAME))

def edit_current_config():
    local_dir = os.path.realpath(os.curdir)
    config_file = find_config(local_dir)

    os.system('vim {}'.format(config_file))
