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

  FILENAME:    Source filename (the child document).
  DESTINATION: Destination directory for compiled html if not specified
               by the <template:destination> tag in the child document.
'''

import re
import sys
import os
from docopt import docopt
from pprint import pprint as pp


def error(msg):
    print(msg)
    sys.exit(1)


def read_file(filename):
    try:
        content = open(filename).read()
    except IOError:
        error('File does not exist: "%s"' % filename)
    return content


def compile_all(A):
    ignore = A.ignore or 'template'
    working_dir = A.filename
    for (dirpath, dirnames, filenames) in os.walk(working_dir):
        # print('>>>', dirpath, dirnames, filenames)
        if os.path.basename(dirpath).startswith(ignore):
            continue
        for f in filenames:
            if f.startswith(ignore):
                continue
            child = os.path.join(dirpath, f)
            final_filename = os.path.basename(child)
            # print(child, '--', final_filename, '--', A.destination)
            compile_one(child, A.destination, final_filename,
                        external_vars=A.vars, do_not_write=A.do_not_write)


def compile_one(child_filename, destination, final_filename,
                external_vars={}, child_data={}, do_not_write=False):
    OPENING = '[['
    CLOSING = ']]'
    ROPENING = '\[\['
    RCLOSING = '\]\]'

    ## read the current file
    current_contents = read_file(child_filename)

    # if [[insert:SOME_FILE]] is in the current file then insert it.
    regex = '{}insert:(.*?){}'.format(ROPENING, RCLOSING)
    all_inserts = re.finditer(regex, current_contents)
    for m in all_inserts:
        insert_content = read_file(m.group(1))
        replace_tag = m.group(0)
        current_contents = current_contents.replace(
            replace_tag, insert_content)

    # replace the %%...%% fields in the content file
    for m in re.finditer(r'%%(.*?)%%', current_contents):
        for val in external_vars:
            if val == m.group(1):
                current_contents = current_contents.replace(
                    m.group(), external_vars[val])

    # fill any [[...]] tags in current file from data in the previous file
    for block_name in child_data:
        dest_tag = '{}{}{}'.format(OPENING, block_name, CLOSING)
        current_contents = current_contents.replace(
            dest_tag, child_data[block_name])

    # remove the parent field so we can stop recursing if
    # there is no more parents
    if 'parent' in child_data:
        del child_data['parent']

    # extract the values from the [[block:...]]...[[/block]]
    # tags in the html file
    re_str = r'{}block:(.*?){}(.*?){}/block{}'.format(
        ROPENING, RCLOSING, ROPENING, RCLOSING)
    all_matches = re.finditer(
        re_str, current_contents, re.MULTILINE | re.DOTALL)

    for m in all_matches:
        tag_name = m.group(1)
        tag_value = m.group(2)
        child_data[tag_name] = tag_value

    # if [[parent:...]] in child:
    parent_filename = re.search(
        '{}parent:(.*?){}'.format(ROPENING, RCLOSING), current_contents)
    if parent_filename:
        child_filename = parent_filename.group(1)
        compile_one(child_filename, destination, final_filename,
                    external_vars=external_vars,
                    child_data=child_data, do_not_write=do_not_write)
    else:
        # delete all unused [[BLOCKS]] and %%EXTERNAL_VARS%%
        regex = "({}.*?{}|%%.*?%%)".format(ROPENING, RCLOSING)
        current_contents = re.sub(regex, '', current_contents)

        # print(destination, final_filename)
        final_filename = os.path.join(destination, final_filename)
        if do_not_write:
            print(current_contents)
        else:
            try:
                dest = open(final_filename, 'w')
            except IOError:
                error('Destination does not exist: "%s"' % (
                    final_filename))
            dest.write(current_contents)
            dest.close()
            print('Created:', final_filename)


def main(args):
    class A:
        filename = os.path.abspath(args['FILENAME'])
        destination = os.path.abspath(args['DESTINATION'])
        ignore = args['--ignore-prefix']
        do_not_write = args['--do-not-write']

        workingdir = os.path.abspath(args['FILENAME'])
        if not os.path.isdir(workingdir):
            workingdir = os.path.dirname(workingdir)

        vars = {}
        for var in args['--var']:
            kv = var.split('::')
            key = kv[0]
            value = kv[1]
            vars[key] = value

    os.chdir(A.workingdir)

    if os.path.isdir(A.filename):
        compile_all(A)

    elif os.path.isfile(A.filename):
        final_filename = os.path.basename(A.filename)
        compile_one(A.filename, A.destination, final_filename,
                    external_vars=A.vars, do_not_write=A.do_not_write)

    else:
        print(A.filename, os.path.curdir)
        error('{} does not exist'.format(A.filename))


if __name__ == '__main__':

    args = docopt(__doc__, version='0.1')
    main(args)
