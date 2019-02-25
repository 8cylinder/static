#!/usr/bin/env python3

r'''
Usage:
  static FILENAME DESTINATION [--var=KEY::VALUE...] [-i IGNORE] [-d]

Options:
  --var=KEY::VALUE...  This can be specified multiple times.  Note that
                       double colons must be used.
  -i PREFIX --ignore-prefix PREFIX
                       Static will ignore any file starting with this
                       prefix, whether it is a file or directory.  Static
                       defaults to ignore anything starting with 'template'
  -d --do-not-write    Output result to screen instead of writing the
                       file to the filesystem

Example:
  html-builder --var='name::John Brown' --var=phone::1234567 \
  content.html ~/projects/site ~/projects/src/html/

Overview:
  FILENAME:    Source filename (the child document)
  DESTINATION: Destination directory for compiled html

  Compile one or all the files in a dir (excluding any set with the -i
  switch).  If the filename is a single file, compile only one, if
  its a dir, compile all.  The default is to ignore any files starting
  with 'template_'.

  This takes a child document and inserts it into a parent document.
  The child document is the FILENAME and the parent is set in the child
  document using [[parent:some/file/name]]

  Values are pass from the child document to the parent by writing
  template tags like this:
  [[block:some_name]]value[[/block]]

  In the parent the value of some_name is put into this field:
  [[some_name]]

  The --var=some_name::value field on the command line will be sent to
  the %%some_name%% field in the parent.

  FILENAME and DESTINATION are required.

  var is an optional key:value formated string that contains replacement
  values for placeholder strings in the html file.  The placeholder
  looks like this: %%placeholder%%
'''

import sys
import os
from docopt import docopt
from static import Static

def error(msg):
    print(msg)
    sys.exit(1)


def main(args):
    filename = os.path.abspath(args['FILENAME'])
    destination = os.path.abspath(args['DESTINATION'])
    ignore = args['--ignore-prefix']
    do_not_write = args['--do-not-write']

    workingdir = os.path.abspath(args['FILENAME'])
    if not os.path.isdir(workingdir):
        workingdir = os.path.dirname(workingdir)

    ext_vars = {}
    for var in args['--var']:
        kv = var.split('::')
        key = kv[0]
        value = kv[1]
        ext_vars[key] = value

    os.chdir(workingdir)

    static = Static()

    if os.path.isdir(filename):
        static.compile_all()

    elif os.path.isfile(filename):
        final_filename = os.path.basename(filename)
        static.compile_one(filename, destination, final_filename,
                           external_vars=ext_vars, do_not_write=do_not_write)

    else:
        print(filename, os.path.curdir)
        error('{} does not exist'.format(filename))


if __name__ == '__main__':

    args = docopt(__doc__, version='0.1')
    main(args)
