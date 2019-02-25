
import re
import os


class StaticError(Exception):
    pass


class Static:
    def __init__(self):
        pass

    def compile_all(self, start_dir, destination, ignore='template',
                    external_vars={}, child_data={}, do_not_write=False):

        for (dirpath, dirnames, filenames) in os.walk(start_dir):
            if os.path.basename(dirpath).startswith(ignore):
                continue
            for f in filenames:
                if f.startswith(ignore):
                    continue
                child = os.path.join(dirpath, f)
                final_filename = os.path.basename(child)
                self.compile_one(child, destination, final_filename,
                                 external_vars=external_vars,
                                 do_not_write=do_not_write)

    def compile_one(self, child_filename, destination, final_filename,
                    external_vars={}, child_data={}, do_not_write=False):

        OPENING = '[['
        CLOSING = ']]'
        ROPENING = '\[\['
        RCLOSING = '\]\]'

        # read the current file
        current_contents = self.read_file(child_filename)

        # if [[insert:SOME_FILE]] is in the current file then insert it.
        regex = '{}insert:(.*?){}'.format(ROPENING, RCLOSING)
        all_inserts = re.finditer(regex, current_contents)
        for m in all_inserts:
            insert_content = self.read_file(m.group(1))
            # throw error if it contains a [[parent:...]] tag
            if '[[parent:' in insert_content:
                msg = 'Inserted documents are not allowed parents: ' + m.group(1)
                raise StaticError(msg)

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
            self.compile_one(child_filename, destination, final_filename,
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
                dest = open(final_filename, 'w')
                # try:
                #     dest = open(final_filename, 'w')
                # except IOError:
                #     error('Destination does not exist: "%s"' % (
                #         final_filename))
                dest.write(current_contents)
                dest.close()
                print('Created:', final_filename)

    def read_file(self, filename):
        content = open(filename).read()
        # try:
        #     content = open(filename).read()
        # except IOError:
        #     error('File does not exist: "%s"' % filename)
        return content



