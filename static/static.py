
import re
import os
import types
import warnings
from pprint import pprint as pp


class StaticError(Exception):
    """Generic error for Static"""
class InsertedParentsError(Exception):
    """Directly inserted documents are not allowed parents"""
class InsertedParentsWarning(UserWarning):
    """Warn about inserts having parents"""

const = types.SimpleNamespace(
    IGNORE='template',
)

class Static:
    def __init__(self, destination, debug=False, strict=True,
                 echo=False):
        """
        destination: dir
        """
        self.debug = True if debug else False
        self.destination = destination
        # self.final_filename = final_filename
        self.OPENING = '[['
        self.CLOSING = ']]'
        self.ROPENING = '\[\['
        self.RCLOSING = '\]\]'
        self.strict = strict
        self.echo = echo

    def compile(self, child_filename, final_filename,
                external_vars={}, child_data={}):
        """
        child_filename  file to read to look for parents
        final_filename  basename of final document
        """
        workingdir = os.path.dirname(child_filename)

        # read the current file
        current_contents = self.read_file(child_filename)

        # if [[insert:SOME_FILE]] is in the current file then insert it.
        current_contents = self.insert_inserts(current_contents, workingdir)

        # replace the %%...%% fields in the content file
        current_contents = self.insert_vars(current_contents, external_vars)

        # fill any [[...]] tags in current file from data in the previous file
        current_contents = self.fill_blocks(current_contents, child_data)

        # remove the parent field so we can stop recursing if
        # there is no more parents
        if 'parent' in child_data:
            del child_data['parent']

        # extract the values from the [[block:...]]...[[/block]]
        # tags in the html file
        re_str = r'{}block:(.*?){}(.*?){}/block{}'.format(
            self.ROPENING, self.RCLOSING, self.ROPENING, self.RCLOSING)
        all_matches = re.finditer(
            re_str, current_contents, re.MULTILINE | re.DOTALL)

        for m in all_matches:
            tag_name = m.group(1)
            tag_value = m.group(2)
            child_data[tag_name] = tag_value

        # if [[parent:...]] in child:
        parent_filename = re.search(
            '{}parent:(.*?){}'.format(self.ROPENING, self.RCLOSING),
            current_contents)

        if parent_filename:
            new_child_filename = os.path.join(
                workingdir, parent_filename.group(1))
            self.compile(new_child_filename, final_filename,
                         external_vars=external_vars,
                         child_data=child_data)
        else:
            # delete all unused [[BLOCKS]] and %%EXTERNAL_VARS%%
            regex = "({}.*?{}|%%.*?%%)".format(self.ROPENING, self.RCLOSING)
            current_contents = re.sub(regex, '', current_contents)

            # print(self.destination, final_filename)
            final_filename = os.path.join(
                self.destination, final_filename)
            if self.echo:
                return current_contents
            else:
                with open(final_filename, 'w') as f:
                    f.write(current_contents)
                print('Created:', final_filename)

    def insert_inserts(self, current_contents, workingdir):
        regex = '{}insert:(.*?){}'.format(self.ROPENING, self.RCLOSING)
        all_inserts = re.finditer(regex, current_contents)
        for m in all_inserts:
            # print('m>>>', m)
            insert_file = os.path.join(workingdir, m.group(1))
            insert_content = self.read_file(insert_file)
            # print('>>>', insert_content, '<<<')

            # throw error if it contains a [[parent:...]] tag
            if '[[parent:' in insert_content:
                msg = 'Inserted documents are not allowed parents: %s' % (
                    m.group(1))
                if self.strict:
                    raise InsertedParentsError(msg)
                else:
                    warnings.warn(msg, InsertedParentsWarning)
                print('!!!!!!!!!!!!!!!!!!!!')
                continue
            replace_tag = m.group(0)
            current_contents = current_contents.replace(
                replace_tag, insert_content)
        return current_contents

    def insert_vars(self, current_contents, external_vars):
        for m in re.finditer(r'%%(.*?)%%', current_contents):
            for val in external_vars:
                if val == m.group(1):
                    current_contents = current_contents.replace(
                        m.group(), external_vars[val])
        return current_contents

    def fill_blocks(self, current_contents, child_data):
        for block_name in child_data:
            dest_tag = '{}{}{}'.format(self.OPENING, block_name, self.CLOSING)
            current_contents = current_contents.replace(
                dest_tag, child_data[block_name])
        return current_contents

    def read_file(self, filename):
        with open(filename) as f:
            content = f.read()
        return content
