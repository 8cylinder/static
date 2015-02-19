#!/usr/bin/env python

r'''
Usage:
  html-builder <filename> <destination> <defaultparent> [--var=<KEY::VALUE>...]

Options:
  --var=<KEY::VALUE>...  This can be specified multiple times.  Note that
                         double colons must be used.

Example:
  html-builder --var='name::John Brown' --var=phone::1234567 \
  content.html ~/projects/site ~/projects/src/html/

filename, destination and defaultparent are required.

var is an optional key:value formated string that contains replacement
values for placeholder strings in the html file.  The placeholder
looks like this: %%placeholder%%

filename:        Source filename
destination:     Destination directory for compiled html
default parent:  The parent html template to use if its not
                 specified in the <template:filename> tag
'''

import re, sys
from docopt import docopt


def main(args):
    content_filename = args['<filename>']
    parent_filename = args['<defaultparent>']
    destination = args['<destination>']

    vars = {}
    if args['--var']:
        for v in args['--var']:
            kv = v.split('::')
            key = kv[0]
            value = kv[1]
            vars[key] = value

    # read the content file
    try:
        content = open(content_filename).read()
    except IOError:
        print 'No such file or directory:', content_filename
        sys.exit(1)

    # replace the %%...%% fields in the content file
    for m in re.finditer(r'%%(.*?)%%', content):
        for val in vars:
            if val == m.group(1):
                content = content.replace(m.group(), vars[val])

    # extract the values from the tags in the html file
    tag_values = {}
    all_matches = re.finditer(r'<template:(.*?)>(.*?)</template:\1>', content)
    for m in all_matches:
        tag_name = m.group(1)
        tag_value = m.group(2)
        content = content.replace(m.group(), '') # delete the tag

        if tag_name == 'filename':
            content_filename = tag_value # override command line
        elif tag_name == 'parent':
            parent_filename = tag_value # override command line
        else:
            tag_values[tag_name] = tag_value

    # read the parent html file
    try:
        frame = open(parent_filename).read()
    except IOError:
        print 'No such file or directory:', parent_filename
        sys.exit(1)

    # replace the %%...%% fields in the parent file
    for m in re.finditer(r'%%(.*?)%%', frame):
        for val in vars:
            if val == m.group(1):
                frame = frame.replace(m.group(), vars[val])

    # insert the content into the parent
    content = content.strip()
    full = frame.replace('[content]', content)

    for v in tag_values:
        dest_tag = '[%s]' % v
        full = full.replace(dest_tag, tag_values[v])


    # write the full html to the file system
    dest = open(destination + '/' + content_filename, 'w')
    dest.write(full)
    dest.close()

    sys.exit()


if __name__ == '__main__':

    args = docopt(__doc__, version='0.1')
    main(args)
