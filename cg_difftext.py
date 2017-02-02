#!/usr/bin/env python2

import os
import string
import sys

__author__ = 'Brian Rzycki <brzycki@gmail.com>'
__license__ = 'Apache License 2.0'
__version__ = '1.0'

def commafy(x):
    """
    Takes an integer on input and converts it to a string with
    commas inserted in the normal place.

    Raises TypeError if input is not an integer.
    """
    if type(x) not in (type(0), type(0L)):
        raise TypeError("Parameter must be an integer.")
    if x < 0:
        return '-' + commafy(-x)
    result = ''
    while x >= 1000:
        x, r = divmod(x, 1000)
        result = ",%03d%s" % (r, result)
    return "%d%s" % (x, result)

class cgFunc(object):
    """
    Contains information related to a single function in the body section
    of a cachegrind output.
    """
    def __init__(self, raw_str, events):
        self.raw_str = raw_str
        self.file_name = None
        self.func_name = None
        self.key = None
        self.found = False
        self.events = events
        self.summary = []
        self.parse()

    def __lt__(self, other):
        """
        This algorithm isn't perfect. It simply parses the metrics in
        whatever sort order they were displayed. Also, less than or
        greater than may differ depending on context. This is a vanilla-
        probably-fine-for-most-cases solution.
        """
        for i in range(len(self.summary)):
            if self.summary[i] < other.summary[i]:
                return True
            elif self.summary[i] > other.summary[i]:
                return False
        return False # every field is the same

    def same_key(self, other):
        """
        Compares if two cgFunc objects have the same key.

        Returns True on success, False otherwise.
        """
        if self.key == None or other.key == None:
            return False
        return self.key == other.key

    def parse(self):
        """
        Parses a raw line of body text into meaningful data for the
        cgFunc object.
        """
        tmp = len(self.events)
        line = self.raw_str.split()
        self.summary = [int(n.replace(',', '')) for n in line[0:tmp]]
        self.key = ' '.join(line[tmp:])
        (self.file_name, _, self.func_name) = self.key.partition(':')

    def diff(self, other):
        """
        Displays a diff of two cgFunc objects with print(). If one of
        the objects is the special "dummy" instance of cgFunc then no
        delta between events is displayed.
        """
        idx = 0
        has_dummy = False
        for f in (self, other):
            if f.key == "_dummy:_dummy":
                has_dummy = True
            else:
                func_name = f.func_name
                file_name = f.file_name
        print("[func] %s\n[file] %s" % (func_name, file_name))
        for name in self.events:
            if has_dummy:
                print("  %4s: %18s %18s" %
                      (name,
                       commafy(self.summary[idx]),
                       commafy(other.summary[idx])))
            else:
                print("  %4s: %18s %18s  [%18s]" %
                      (name,
                       commafy(self.summary[idx]),
                       commafy(other.summary[idx]),
                       commafy(other.summary[idx] - self.summary[idx])))
            idx += 1

class cgFile(object):
    """
    Contains information related to a single cachegrind text file
    of a cachegrind output.
    """
    def __init__(self, file_name):
        self.file_name = file_name
        self.metadata = {}
        self.events = []
        self.summary = []
        self.funcs = []
        self.parse()

    def parse(self):
        """
        Parses the complete cachegrind text file and converts it to meaningful
        data.
        """
        location = 'start'
        for line in open(self.file_name, 'r'):
            line = line.strip()
            if not line:
                continue
            if location == 'start':
                if line.startswith('--'):
                    location = 'metadata'
                    continue
            elif location == 'metadata':
                if line.startswith('--'):
                    self.events = self.metadata['Event sort order'].split()
                    location = 'summary header'
                    continue
                line = line.split(':')
                tmp = line[1].strip()
                if not tmp:
                    continue
                self.metadata[line[0].strip()] = tmp
            elif location == 'summary header':
                if line.startswith('--'):
                    location = 'summary'
                    continue
            elif location == 'summary':
                if line.startswith('--'):
                    location = 'body header'
                    continue
                self.summary = [int(n.replace(',', '')) for n in line.split()[:-2]]
            elif location == 'body header':
                if line.startswith('--'):
                    location = 'body'
                    continue
            elif location == 'body':
                tmp = cgFunc(line, self.events)
                if tmp.key != '???:???':
                    self.funcs.append(tmp)

    def same_metadata(self, other):
        """
        Compares the metadata regions of two cgFile objects. This routine
        ignores some fields that will be different even when captured
        in the same way.

        Returns True if they are the same, False otherwise.
        """
        for key in self.metadata.keys():
            if key == 'Data file':
                continue
            if self.metadata[key] != other.metadata[key]:
                return False
        return True

    def diff_summary(self, other):
        """
        Displays a diff of the PROGRAM TOTALS using print() between
        two cgFile objects.
        """
        print("[file_a] %s" % self.metadata['Data file'])
        print("[file_b] %s" % other.metadata['Data file'])
        idx = 0
        for name in self.events:
            print("  %4s: %18s %18s  [%18s]" %
                  (name,
                   commafy(self.summary[idx]),
                   commafy(other.summary[idx]),
                   commafy(other.summary[idx] - self.summary[idx])))
            idx += 1
        print("")

    def diff_body(self, other):
        """
        Displays the diff of every function in the body section of two
        cgFiles. The output is from max to min (see __le__ in cgFunc)
        and matched pairs are displayed inline with routines found only
        in one file.
        """
        pairs = []
        # generate a dummy func to pair with solo funcs
        dummy = cgFunc(('0 ' * len(self.events)) + "_dummy:_dummy",
                       self.events)
        for func in self.funcs:
            for func2 in other.funcs:
                if func2.found:
                    continue
                elif func.same_key(func2):
                    pairs.append((func, func2))
                    func.found = func2.found = True
        for func in self.funcs:
            if not func.found:
                pairs.append((func, dummy))
                func.found = True
        for func in other.funcs:
            if not func.found:
                pairs.append((dummy, func))
                func.found = True
        pairs = sorted(pairs, key=lambda x: max(x[0], x[1]), reverse=True)
        for (func, func2) in pairs:
            func.diff(func2)
            print("")

def main(a, b):
    """
    Main routine. Both a and b are paths to text files generated
    the following steps:
      valgrind --tool=cachegrind ./foo --cachegrind-out-file=foo.out
      cg_annotate foo.out > foo_out.txt

    Returns an integer suitable for a unix process $? return code.
    """
    for i in (a, b):
        if not os.path.isfile(i):
            print('file "%s" not found.' % i)
            return 1
    cg_a = cgFile(a)
    cg_b = cgFile(b)

    if not cg_a.same_metadata(cg_b):
        print('metadata does not match.')
        return 0

    cg_a.diff_summary(cg_b)
    cg_a.diff_body(cg_b)
    return 0

if __name__ == '__main__':
    try:
        (a, b) = sys.argv[1:3]
    except (IndexError, ValueError):
        print('usage: cg_difftext.py file_a file_b')
        sys.exit(1)
    sys.exit(main(a, b))
