import os


# ------------------------------------------------------------------------------
# Global Constants
# ------------------------------------------------------------------------------

"""Name of the directories that contains the reporitory data."""
COMMAND_DIR = 'commands'
CONTEXT_DIR = 'contexts'
REPO_DIR = '.prm'


"""Name of configuration files."""
CONTEXTLIST_FILE = 'CONTEXTLIST'
LOG_FILE = 'LOG'
SETTINGS_FILE = 'SETTINGS'


# ------------------------------------------------------------------------------
# Helper Methods
# ------------------------------------------------------------------------------

def init_repository():
    """Initialize an experiment repository by creating the required folders
    and files.

    Raises RuntimeError if a repository directory already exists in the current
    working directory.
    """
    # Make sure that no project directory exists in the current directory and
    # that there is no project directory along the path to the root.
    if os.path.isfile(REPO_DIR) or os.path.isdir(REPO_DIR):
        raise RuntimeError('existing repository detected')
    parent, name = os.path.split(os.path.abspath('.'))
    while not parent is None:
        if os.path.isdir(os.path.join(parent, REPO_DIR)):
            raise RuntimeError('existing repository detected in \'' + parent + '\'')
        if parent == '/':
            parent = None
        else:
            parent, name = os.path.split(parent)
    os.mkdir(REPO_DIR)
    os.mkdir(os.path.join(REPO_DIR, COMMAND_DIR))
    os.mkdir(os.path.join(REPO_DIR, CONTEXT_DIR))
    open(os.path.join(REPO_DIR, CONTEXTLIST_FILE), 'a').close()
    open(os.path.join(REPO_DIR, LOG_FILE), 'a').close()
    open(os.path.join(REPO_DIR, SETTINGS_FILE), 'a').close()
