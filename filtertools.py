import os
import os.path
from collections import OrderedDict


def make_filters_args(config):
    options = []
    if config.get('filters'):
        for filter in config['filters'].split('\n'):
            if filter != '':
                options += ('--filter', filter)

    if config.get('select_dirs'):
        dirs = [dir for dir in config['select_dirs'].split('\n') if dir != '']
        for filter in parse_select_dirs(dirs):
            options += ('--filter', filter)
    return options


def _add_filters(dir_base,  dir_leaf,  filters):
    for dir,  sub in dir_leaf.items():
        path = os.path.join(dir_base,  dir) + os.sep
        filters.append('+ '+path)
        if len(sub) > 0:
            _add_filters(path,  sub, filters)
            filters.append('P '+path + '*')
            filters.append('- '+path + '*')
        
def _make_dir_tree(dirs):
    dir_tree = {}
    for dir in dirs:
        dir = dir.strip(os.sep)
        dir_leaf = dir_tree
        for d in dir.split(os.sep):
            dir_leaf = dir_leaf.setdefault(d,  dict())

def _remove_overlapping_dirs(dirs):
    dirs = sorted(dirs)
    i = 0
    while i < len(dirs)-1:
        if dirs[i+1].startswith(dirs[i]):
            del dirs[i+1]
        else:
            i += 1
    return dirs
        
def parse_select_dirs(dirs):
    dir_tree = OrderedDict()
    strip_dirs = [dir.strip(os.sep) for dir in dirs]
    strip_dirs = _remove_overlapping_dirs(strip_dirs)
    for dir in strip_dirs:
        dir_leaf = dir_tree
        for d in dir.split(os.sep):
            dir_leaf = dir_leaf.setdefault(d,  OrderedDict())
        # Remove all sub-dirs
        dir_leaf.clear()
    filters = []
    _add_filters('/',  dir_tree, filters)
    if  len(filters) > 0:
            filters.append('P /*')
            filters.append('- /*')
    return filters
    
import unittest

class TestFilterArgs(unittest.TestCase):

    def test_empty(self):
        self.assertEqual(make_filters_args({}), [])

    def test_top_dir(self):
        self.assertEqual(parse_select_dirs(['a',  '/b',  '/c/']),
                         ['+ /a/', '+ /b/', '+ /c/',  'P /*',  '- /*'])

    def test_inner_dir(self):
        self.assertEqual(parse_select_dirs(['/a/b/c']), 
                ['+ /a/', '+ /a/b/', '+ /a/b/c/',  'P /a/b/*',  '- /a/b/*', 'P /a/*',  
                '- /a/*',  'P /*',  '- /*'])

    def test_parse_overlap(self):
        self.assertEqual(parse_select_dirs(['/a/b/c', '/a']), 
                ['+ /a/',  'P /*',  '- /*'])

    def test_subdirs1(self):
        self.assertEqual(parse_select_dirs(['/a/b',  '/a/c',  '/a/b/c']), 
                ['+ /a/', '+ /a/b/', '+ /a/c/', 'P /a/*', '- /a/*', 'P /*', '- /*'])

    def test_subdirs2(self):
        self.assertEqual(parse_select_dirs(['/a/b/d',  '/a/c',  '/a/b/c']), 
                ['+ /a/', '+ /a/b/', '+ /a/b/c/', '+ /a/b/d/', 'P /a/b/*', '- /a/b/*', 
                '+ /a/c/', 'P /a/*', '- /a/*', 'P /*', '- /*'])

if __name__ == '__main__':
    unittest.main()
