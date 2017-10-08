"""Context manager."""

import os
import uuid
import yaml

import prmcore.config as conf


class ContextManager(object):
    def __init__(self, work_dir):
        if not os.path.isdir(work_dir):
            raise ValueError('not a directory \'' + work_dir + '\'')
        abs_dir = os.path.abspath(work_dir)
        self.work_dir = abs_dir
        # Get the project directory and the relative path from the project
        # directory to the working directory. Ensure that REPO_DIR is not part
        # of the working directory path
        self.project_dir = None
        self.path = []
        if os.path.isdir(os.path.join(abs_dir, conf.REPO_DIR)):
            self.project_dir = os.path.join(abs_dir, conf.REPO_DIR)
        else:
            parent, name = os.path.split(os.path.abspath(work_dir))
            while self.project_dir is None:
                if name == conf.REPO_DIR:
                    raise ValueError('invalid working directory \'' + work_dir + '\'')
                self.path.append(name)
                if os.path.isdir(os.path.join(parent, conf.REPO_DIR)):
                    self.project_dir = os.path.join(parent, conf.REPO_DIR)
                elif parent == '/':
                    break
                else:
                    parent, name = os.path.split(parent)
        # Raise exception if no project directory was found
        if self.project_dir is None:
            raise ValueError('not under project repository \'' + work_dir + '\'')
        # IMPORTANT! Reverse the path listing
        self.path = list(reversed(self.path))
        # Ensure that the project directory contains all expected sub-folders
        # and files
        self.cmd_dir = is_dir(self.project_dir, conf.COMMAND_DIR)
        self.context_dir = is_dir(self.project_dir, conf.CONTEXT_DIR)
        self.contextls_file = is_file(self.project_dir, conf.CONTEXTLIST_FILE)
        self.log_file = is_file(self.project_dir, conf.LOG_FILE)
        self.settings_file = is_file(self.project_dir, conf.SETTINGS_FILE)

    def context_settings(self):
        """Get settings for the current context.

        Returns
        -------
        prjrepo.config.context.Config
        """
        return Config(self.get_context_files(), False)

    def create_context(self):
        """Create a new context for the current working directory.

        Raises RuntimeError if a context for the working directory already
        exists or if the working directory is the project directory.
        """
        # Ensure that the working directiry is not the project base directory
        if len(self.path) == 0:
            raise RuntimeError('cannot create context in project base')
        # Get the relative path to the working directory
        rel_path = '/'.join(self.path)
        # A context exists if the last element in the context files list refers
        # to the relative path
        if self.get_context_files()[-1][0] == rel_path:
            raise RuntimeError('context already exists for \'' + rel_path + '\'')
        # Append entry for new context to context listing file
        context_id = str(uuid.uuid4()).replace('-', '')
        while os.path.isfile(os.path.join(self.context_dir, context_id + '.yaml')):
            context_id = str(uuid.uuid4()).replace('-', '')
        with open(self.contextls_file, 'a') as f:
            f.write(rel_path + '\t' + context_id + '.yaml\n')

    def get_context_files(self):
        """Get a list of context files along the path from the project directory
        to the working directory. The first entry is a reference to the settings
        file for the project.

        The list elements are tuples with the first element being the path to
        the conext and the second element the absolute path to the settings
        file.

        Returns
        -------
        list((string, string))
        """
        contexts = read_contexts(self.contextls_file)
        context_files = list()
        context_files.append(('', self.settings_file))
        if len(self.path) > 0:
            for i in range(1, len(self.path) + 1):
                key = '/'.join(self.path[:i])
                if key in contexts:
                    context_files.append(
                        (key, os.path.join(self.context_dir, contexts[key]))
                    )
        return context_files

    def locate_input_file(self, name, is_file):
        """Locate an input file (ordirectory) in the context path. Returns the
        first resource that matches the given name (i.e., relative path). The
        search progresses from the context directory down to the project
        directory.

        Raises ValueError if no matching resource is found or if the resource
        is not of the expected type.

        Parameters
        ----------
        name: string
            Relative path of file or directory
        is_file: bool
            Flag indicating whether the resource should be a file (True) or a
            directory (False).

        Returns
        -------
        string
        """
        base_dir = self.work_dir
        i = 0
        while i <= len(self.path):
            f_path = os.path.join(base_dir, name)
            if is_file and os.path.isfile(f_path):
                return os.path.relpath(f_path, self.work_dir)
            elif not is_file and os.path.isdir(f_path):
                return os.path.relpath(f_path, self.work_dir)
            elif os.path.isfile(f_path) or os.path.isdir(f_path):
                raise ValueError('unexpected type \'' + f_path + '\'')
            i += 1
            base_dir, dir_name = os.path.split(base_dir)
        raise ValueError('file not found \'' + name + '\'')

    def project_settings(self):
        """Get project settings for the context's project.

        Returns
        -------
        prjrepo.config.context.Config
        """
        return Config([('', self.settings_file)], True)


class Config(object):
    """Object excapsulating context settings."""
    def __init__(self, settings, is_project_config):
        """Initialize the settings dictionary from the given dictionary and an
        optional dictionary containing default values.

        Parameters
        ----------
        settings: list((string, string))
            List of context settings along the path from the project base
            directory to a given context. List elements are tuples where the
            first value is the relative path expression and the second value is
            a reference to the context file.
        is_project_config: bool
            Flag indicating whether this object represents the project settings
            or settings for a project context.
        """
        self.files = settings
        self.is_project_config = is_project_config

    def get_value(self, para, default_values=dict()):
        """Return the value that is associated with the given parameter. The
        parameter expression can be a path expression.

        Raises ValueError if the specified parameter does not exist or if it
        references an internal dictionary in the nested settings dictionary.

        Parameters
        ----------
        para: string
            Configuration parameter expression

        Returns
        -------
        string
        """
        return get_settings_value(self.settings, para, default_values=default_values)

    @property
    def settings(self):
        settings = read_settings(self.files[0][1])
        for i in range(1, len(self.files)):
            settings = nested_merge(
                settings, read_settings(self.files[i][1])
            )
        return settings

    def update_value(self, para, value=None, cascade=False):
        """Update the value of a configuration parameter. The para argument may
        contain a path expression. In this case all nested elements along the
        path are created if necessary.

        If the given value is None the parameter will be deleted.

        Raises ValueError if an invalid parameter name is given or if an
        existing text element is referenced as part of a path expression.

        Parameters
        ----------
        para: string
            Parameter path
        value: string, optional
            New parameter value or None (indicating delete)
        cascade: bool, optional
            If True the change cascades to all context files (except the
            project settings)
        """
        path = para.split('.')
        key = path[-1].strip()
        if key == '':
            raise ValueError('invalid parameter name \'' + para + '\'')
        if cascade and not self.is_project_config:
            start = 1
        else:
            start = len(self.files) - 1
        for i in range(start, len(self.files)):
            filename = self.files[i][1]
            settings = read_settings(filename)
            el = settings
            # Find the element that is referenced by the path prefix. Create
            # elements along the path if necessary (only if not deleting)
            for comp in path[:-1]:
                if not comp in el:
                    if not value is None:
                        el[comp] = dict()
                    else:
                        break
                el = el[comp]
                if not isinstance(el, dict):
                    raise ValueError('cannot create element under text value \'' + el + '\'')
            # Update the parameter value in the target element or delete the element if
            # the given value is None
            if not value is None:
                el[key] = value
            elif not el is None:
                if key in el:
                    del el[key]
            # Write the modified settings to the context file
            with open(filename, 'w') as f:
                yaml.dump(settings, f, default_flow_style=False)



# ------------------------------------------------------------------------------
# Helper Methods
# ------------------------------------------------------------------------------

def get_settings_value(settings, para, var_list=[], default_values=dict()):
    el = settings
    for comp in para.split('.'):
        if isinstance(el, dict):
            if comp in el:
                el = el[comp]
            elif para in default_values:
                return default_values[para]
            else:
                return None
        else:
            raise ValueError('cannot get value of \'' + para + '\'')
    if not isinstance(el, dict):
        if isinstance(el, basestring):
            return resolve_variables(settings, el, var_list, default_values)
        else:
            return el
    else:
        raise ValueError('cannot get value of \'' + para + '\'')


def is_dir(parent, sub_folder):
    """Raise RuntimeError if the given sub-folder is not an existing directory
    under the parent directory.

    Returns the path to the sub-folder if it exists.

    Parameters
    ----------
    parent: string
        Path to parent directory
    sub_folder: string
        Sub-folder name

    Returns
    -------
    string
    """
    dir_path = os.path.join(parent, sub_folder)
    if not os.path.isdir(dir_path):
        raise RuntimeError('sub-folder \'' + sub_folder + '\' does not exist')
    return dir_path


def is_file(parent, filename):
    """Raise RuntimeError if the given file is not an existing file under the
    parent directory.

    Returns the path to the file if it exists.

    Parameters
    ----------
    parent: string
        Path to parent directory
    filename: string
        Name of file in parent directory

    Returns
    -------
    string
    """
    file_path = os.path.join(parent, filename)
    if not os.path.isfile(file_path):
        raise RuntimeError('file \'' + filename + '\' does not exist')
    return file_path


def nested_merge(d1, d2):
    """Merge two dictionaries such that d1 will contain all the values from d2.

    Parameters
    ----------
    d1: dict
        Dictionary into which the second dictionary is merged
    d2: dict
        Dictionary of values that are merged into the first dictionary.

    Returns
    -------
    dict
    """
    for key in d2:
        if not key in d1:
            d1[key] = d2[key]
        elif isinstance(d1[key], dict) and isinstance(d2[key], dict):
            d1[key] = nested_merge(d1[key], d2[key])
        else:
            d1[key] = d2[key]
    return d1


def read_contexts(filename):
    """Read the projects context listing. Returns a dictionary where the keys
    are path expressions to project sub-directories and the values are context
    settings file names.

    Returns
    -------
    dict
    """
    contexts = dict()
    with open(filename, 'r') as f:
        for line in f:
            tokens = line.strip().split('\t')
            if len(tokens) == 2:
                contexts[tokens[0]] = tokens[1]
    return contexts


def read_settings(filename):
    """Read settings from the given file. Expets the file content to be in Yaml
    format. Returns an empty dictionary if the file does not exist.

    Parameters
    ----------
    filename: string
        Path to the input Yaml file

    Returns
    -------
    dict
    """
    # Read the settings file if it exist. Otherwise return an empty dictionary.
    if os.path.isfile(filename):
        with open(filename, 'r') as f:
            obj = yaml.load(f.read())
            if obj is None:
                obj = dict()
            return obj
    else:
        return dict()


def resolve_variables(settings, value, var_list, default_values):
    while '[[' in value:
        i_start = value.find('[[')
        i_end = value.find(']]', i_start)
        if i_end == -1:
            raise ValueError('invalid variable expression \'' + value + '\'')
        var_name = value[i_start+2:i_end]
        if var_name in var_list:
            raise ValueError('recursive reference for \'' + var_list[0] + '\'')
        var_list.append(var_name)
        val = get_settings_value(settings, var_name, var_list=var_list, default_values=default_values)
        var_list.pop()
        value = value[:i_start] + val + value[i_end+2:]
    return value
