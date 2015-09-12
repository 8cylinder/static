#!/usr/bin/env python

r'''
Usage:
  static FILENAME DESTINATION [--var=KEY::VALUE...] [-i IGNORE]

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

  FILENAME:    Source filename (the child document).
  DESTINATION: Destination directory for compiled html if not specified
               by the <template:destination> tag in the child document.
'''

import re, sys, os
from docopt import docopt
from pprint import pprint as pp

def error(msg):
    print msg
    sys.exit(1)

def read_file(filename):
    try:
        content = open(filename).read()
    except IOError:
        error('File does not exist: "%s"' % content_filename)
    return content

def compile_all(A):
    ignore = A.ignore or 'template_'
    d = A.filename
    for (dirpath, dirnames, filenames) in os.walk(d):
        for f in filenames:
            if f.startswith(ignore): continue
            child = os.path.join(dirpath, f)
            A.filename = child
            A.workingdir = dirpath
            compile_one(A.filename, A.destination, A.filename,
                        external_vars=A.vars)

def compile_one(child_filename, destination, final_filename,
                external_vars={}, child_data={}):
    OPENING = '[['
    CLOSING = ']]'
    ROPENING = '\[\['
    RCLOSING = '\]\]'

    child_contents = read_file(child_filename)

    # if [[insert:SOME_FILE]]: insert it.
    regex = '{}insert:(.*?){}'.format(ROPENING, RCLOSING)
    all_inserts = re.finditer(regex, child_contents)
    for m in all_inserts:
        insert_content = read_file(m.group(1))
        replace_tag = m.group(0)
        child_contents = child_contents.replace(
            replace_tag, insert_content)

    # replace the %%...%% fields in the content file
    for m in re.finditer(r'%%(.*?)%%', child_contents):
        for val in external_vars:
            if val == m.group(1):
                child_contents = child_contents.replace(
                    m.group(), external_vars[val])

    # fill any [[BLOCKS]] in child doc
    for block_name in child_data:
        dest_tag = '{}{}{}'.format(OPENING, block_name, CLOSING)
        child_contents = child_contents.replace(
            dest_tag, child_data[block_name])

    # remove the parent field so we can stop recursing if
    # there is no more parents
    if 'parent' in child_data:
        del child_data['parent']

    # extract the values from the <template:...>
    # tags in the html file
    all_matches = re.finditer(
        r'<template:(.*?)>(.*?)</template:\1>',
        child_contents, re.MULTILINE|re.DOTALL)

    for m in all_matches:
        tag_name = m.group(1)
        tag_value = m.group(2)
        # if a tag name matches an older one, don't set it because
        # we want the value closest to the begining to take
        # presidence over later ones if tag_name in
        # child_data: continue
        child_data[tag_name] = tag_value

    if 'parent' in child_data:
        child_filename = child_data['parent']
        compile_one(child_filename, destination, final_filename,
                    external_vars=external_vars,
                    child_data=child_data)
    else:
        # delete all unused [[BLOCKS]] and %%EXTERNAL_VARS%%
        regex = "({}.*?{}|%%.*?%%)".format(ROPENING, RCLOSING)
        child_contents = re.sub(regex, '', child_contents)

        final_filename = os.path.join(destination, final_filename)
        try:
            dest = open(final_filename, 'w')
        except IOError:
            error('Destination does not exist: "%s"' % (
                final_filename))
        dest.write(child_contents)
        dest.close()


def main(args):
    class A:
        filename = args['FILENAME']
        destination = args['DESTINATION']
        ignore = args['--ignore-prefix']
        workingdir = os.path.dirname(args['FILENAME'])
        vars = {}
        for var in args['--var']:
            kv = var.split('::')
            key = kv[0]
            value = kv[1]
            vars[key] = value

    if os.path.isdir(A.filename):
        compile_all(A)

    elif os.path.isfile(A.filename):
        compile_one(A.filename, A.destination,
                    A.filename, external_vars=A.vars)

    else:
        error('%s does not exist' % name)


if __name__ == '__main__':

    args = docopt(__doc__, version='0.1')
    main(args)
