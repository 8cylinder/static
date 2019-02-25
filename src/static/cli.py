#!/usr/bin/env python3

import os
import sys
import warnings
from pprint import pprint as pp
import click
from static import Static
from static import const
from static import InsertedParentsError
from static import InsertedParentsWarning

__version__ = '0.1'

CONTEXT_SETTINGS = {
    # add -h in addition to --help
    'help_option_names': ['-h', '--help'],
    # allow case insensitive commands
    'token_normalize_func': lambda x: x.lower(),
}


@click.command(context_settings=CONTEXT_SETTINGS)
@click.argument('filename', type=click.Path(
    exists=True, dir_okay=True, resolve_path=True))
@click.argument('destination', type=click.Path(
    exists=True, file_okay=False, writable=True, resolve_path=True))
@click.option('--ignore', '-i', default=const.IGNORE,
              help=("Static will ignore any file starting with this "
                    "prefix, whether it is a file or directory.  Static's "
                    "defaults is to ignore anything starting with '%s'") %
              const.IGNORE)
@click.option('--echo', '-d', is_flag=True,
              help=("Output results to screen instead of writing"
                    "the file to the filesystem"))
@click.option('--var', multiple=True, type=(str, str),
              help=("This is two arguments space seperated, and "
                    "can be used multiple times."))
@click.option('--strict/--not-strict', default=True,
              help=("Halt if fields are left unused."))
@click.version_option(version=__version__)
def static(filename, destination, ignore, echo, var, strict):
    """
    Template system to dynamicaly build static webpages.

    \b
    FILENAME:    Source filename (the child document)
    DESTINATION: Destination directory for compiled html

    Compile one or all the files in a dir (excluding any set with the -i
    switch).  If the filename is a single file, compile only one, if
    its a dir, compile all.  The default is to ignore any files or dirs
    starting with 'template'.

    This takes a child document and inserts it into a parent document.
    The child document is the FILENAME and the parent is set in the child
    document using [[parent:some/file/name]]

    Values are pass from the child document to the parent by writing
    template tags like this:
    [[block:some_name]]value[[/block]]

    In the parent the value of some_name is put into this field:
    [[some_name]]

    The `--var key value` field on the command line will be sent to
    the %%key%% field in the parent.

    Also external documents can be inserted with: [[insert:some/file/name]].
    They can contain %%var%% fields, but cannot have parents.

    var is an optional 'key value' formated string that contains replacement
    values for placeholder strings in the html file.  The placeholder
    looks like this: %%placeholder%%

    \b
    Example:
      static index.html ~/projects/dist \\
      --var=name 'John Brown' --var=phone 1234567
    """
    ext_vars = dict(var)
    static = Static(destination, strict=strict, echo=echo)

    if os.path.isdir(filename):
        children = find_templates(filename)
    else:
        children = [filename]

    warnings.filterwarnings("error")
    for child in children:
        final_filename = os.path.basename(filename)
        final_filename = os.path.join(destination, final_filename)
        try:
            static(destination, final_filename, child,
                   external_vars=ext_vars, strict=strict, echo=echo)
            static.compile(child, final_filename,
                           external_vars=ext_vars)
        except InsertedParentsError as e:
            sys.exit(e)
        except InsertedParentsWarning as e:
            print(e)

        print('done')


def find_templates(start, ignore=const.IGNORE):
    '''Find all non template files in tree'''
    allfiles = []
    for (dirpath, dirnames, filenames) in os.walk(start):
        if os.path.basename(dirpath).startswith(ignore):
            continue
        for f in filenames:
            if f.startswith(ignore):
                continue
            child = os.path.join(dirpath, f)
            final_filename = os.path.basename(child)
            allfiles.append([final_filename, child])
    pp(allfiles)
    return allfiles


if __name__ == '__main__':

    filename = ''
    destination = ''
    ignore = ''
    do_not_write = ''
    workingdir = ''
    static(filename, destination, ignore, do_not_write, workingdir)
