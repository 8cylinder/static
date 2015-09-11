#!/usr/bin/env python

r'''
Usage:
  static FILENAME [DESTINATION] [DEFAULTPARENT] [--var=KEY::VALUE...] [-i IGNORE]

Options:
  --var=KEY::VALUE...  This can be specified multiple times.  Note that
                       double colons must be used.
  -i PREFIX --ignore-prefix PREFIX
                       Static will ignore any file starting with

Example:
  html-builder --var='name::John Brown' --var=phone::1234567 \
  content.html ~/projects/site ~/projects/src/html/

Overview:
  Compile one or all the files in a dir (excluding any set with the -i
  switch).  If the filename is a single file, compile only one, if
  its a dir, compile all.  The default is to ignore any files starting
  with 'template_'.

  This takes a child document and inserts it into a parent document.
  The child document is the FILENAME and the parent is the
  DEFAULTPARENT or from inside of the child document.  The parent
  must have a [[content]] field in it.  This is where the child
  document is inserted.

  Values are pass from the child document to the parent by writing
  template tags like this:
  <template:some_name>value</template:some_name>

  In the parent the value of some_name is put into this field:
  [[some_name]]

  The --var=some_name::value field on the command line will be sent to
  the %%some_name%% field in the parent.

  FILENAME is required and the DESTINATION and DEFAULTPARENT can be
  specified on the command line or from inside of the child document.

  var is an optional key:value formated string that contains replacement
  values for placeholder strings in the html file.  The placeholder
  looks like this: %%placeholder%%

  FILENAME:       Source filename (the child document).
  DESTINATION:    Destination directory for compiled html if not specified
                  by the <template:destination> tag in the child document.
  DEFAULTPARENT:  The parent html template to use if its not specified by
                  the <template:parent> tag in the child document.
'''

import re, sys, os
from docopt import docopt
from pprint import pprint as pp

def error(msg):
    print msg
    sys.exit(1)

def compile_all(A):
    ignore = A.ignore or 'template_'
    d = A.filename
    for (dirpath, dirnames, filenames) in os.walk(d):
        for f in filenames:
            if f.startswith(ignore): continue
            child = os.path.join(dirpath, f)
            A.filename = child
            A.workingdir = dirpath
            #pp(vars(A))
            compile_one(A)

def compile_one(A):
    content_filename = A.filename
    parent_filename = A.defaultparent
    destination = A.destination

    vars = {}
    if A.var:
        for v in A.var:
            kv = v.split('::')
            key = kv[0]
            value = kv[1]
            vars[key] = value

    # read the content file
    try:
        content = open(content_filename).read()
    except IOError:
        error('Content file does not exist: "%s"' % content_filename)

    # replace the %%...%% fields in the content file
    for m in re.finditer(r'%%(.*?)%%', content):
        for val in vars:
            if val == m.group(1):
                content = content.replace(m.group(), vars[val])

    # extract the values from the tags in the html file
    tag_values = {}
    all_matches = re.finditer(r'<template:(.*?)>(.*?)</template:\1>',
                              content, re.MULTILINE|re.DOTALL)
    for m in all_matches:
        tag_name = m.group(1)
        tag_value = m.group(2)
        content = content.replace(m.group(), '') # delete the tag

        # check in the child doc if vars are set there
        if tag_name == 'filename':
            content_filename = tag_value # override command line
        elif tag_name == 'parent':
            parent_filename = tag_value # override command line
        elif tag_name == 'destination':
            destination = tag_value
        else:
            tag_values[tag_name] = tag_value

    if not content_filename or not parent_filename or not destination:
        print('ERROR: %s' % content_filename)
        print('  Required variables are not set:')
        #print('    filename:    "%s"' % content_filename)
        print('    parent:      "%s"' % parent_filename)
        print('    destination: "%s"' % destination)
        return

    # read the parent html file
    parent_filename = os.path.join(A.workingdir, parent_filename)
    try:
        frame = open(parent_filename).read()
    except IOError:
        error('Parent file does not exist: "%s"' % parent_filename)

    # replace the %%...%% fields in the parent file
    for m in re.finditer(r'%%(.*?)%%', frame):
        for val in vars:
            if val == m.group(1):
                frame = frame.replace(m.group(), vars[val])

    for v in tag_values:
        dest_tag = '[[%s]]' % v
        full = full.replace(dest_tag, tag_values[v])

    # now remove all unused [[.*]] fields
    full = re.sub('\[\[.*?\]\]', '', full)

    # write the full html to the file system
    destination = os.path.normpath(os.path.join(A.workingdir, destination, content_filename))
    try:
        dest = open(destination, 'w')
    except IOError:
        error('Destination does not exist: "%s/%s"' % (destination, content_filename))
    dest.write(full)
    dest.close()

    print 'Done:', content_filename, destination

def main(args):
    class A:
        filename = args['FILENAME']
        destination = args['DESTINATION']
        defaultparent = args['DEFAULTPARENT']
        ignore = args['--ignore-prefix']
        var = args['--var']
        workingdir = os.path.dirname(args['FILENAME'])

    if os.path.isdir(A.filename):
        compile_all(A)
    elif os.path.isfile(A.filename):
        compile_one(A)
    else:
        error('%s does not exist' % name)


if __name__ == '__main__':

    args = docopt(__doc__, version='0.1')
    main(args)
