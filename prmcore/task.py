from abc import abstractmethod


class InstallTask(object):
    """Task in an installation sequence for a package module. Individual tasks
    are executed in order of appearance in the installation script.
    """
    @abstractmethod
    def execute(self, config, upgrade=False):
        """Execute a specific installation task. The installation environment is
        defined by the given context settings.

        Parameters
        ----------
        config: Config
            Configuration variables
        upgrade: bool
            Indicate whether the install is an ugrade of an existing
            installation.
        """
        pass


class DownloadTask(InstallTask):
    def execute(self, config, upgrade=False):
        """Execute a specific installation task. The installation environment is
        defined by the given context settings.

        Parameters
        ----------
        config: Config
            Configuration variables
        upgrade: bool
            Indicate whether the install is an ugrade of an existing
            installation.
        """
        pass
    
