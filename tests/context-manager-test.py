import os
import unittest
import yaml


import prjrepo.config as conf
from prjrepo.config.context import ContextManager
from prjrepo.workflow.repository import DefaultCommandRepository


PROJECT_DIR = './.prm'
WORK_DIR = './db'
SUB_DIR = './db/sub'


class TestContextManager(unittest.TestCase):

    def setUp(self):
        """Initialize settings files."""
        with open(os.path.join(PROJECT_DIR, conf.SETTINGS_FILE), 'w') as f:
            yaml.dump({'a' : 1, 'b': 2}, f, default_flow_style=False)
        context_dir = os.path.join(PROJECT_DIR, conf.CONTEXT_DIR)
        if not os.path.isdir(context_dir):
            os.makedirs(context_dir)
        with open(os.path.join(context_dir, 'A.yaml'), 'w') as f:
            yaml.dump({'b' : 1, 'c': 2}, f, default_flow_style=False)
        with open(os.path.join(PROJECT_DIR, conf.CONTEXTLIST_FILE), 'w') as f:
            f.write('db\tA.yaml\n')

    def test_create_context(self):
        """Test creation of new context in sub-folder"""
        context = ContextManager(SUB_DIR)
        context.create_context()
        with self.assertRaises(RuntimeError):
            ContextManager(WORK_DIR).create_context()
        with self.assertRaises(RuntimeError):
            ContextManager('.').create_context()

    def test_get_settings(self):
        """Get settings for context."""
        for directory in [WORK_DIR, SUB_DIR]:
            settings = ContextManager(directory).context_settings()
            self.assertEquals(settings.get_value('a'), 1)
            self.assertEquals(settings.get_value('b'), 1)
            self.assertEquals(settings.get_value('c'), 2)
            settings = ContextManager(directory).project_settings()
            self.assertEquals(settings.get_value('a'), 1)
            self.assertEquals(settings.get_value('b'), 2)

    def test_invalid_work_directory(self):
        """Test context manager initialization with invalid working directory.
        """
        with self.assertRaises(ValueError):
            ContextManager(os.path.join(WORK_DIR, 'somedir'))
        with self.assertRaises(ValueError):
            ContextManager('..')

    def test_list_context_commands(self):
        """Command to execute SQL query that lists datasets."""
        for directory in [WORK_DIR, SUB_DIR]:
            commands = DefaultCommandRepository(
                ContextManager(directory).cmd_dir
            ).list_commands()
            self.assertTrue('list-datasets' in commands)
            self.assertTrue('run-java' in commands)

    def test_update_values(self):
        """Test creation of new context in sub-folder"""
        context = ContextManager(SUB_DIR)
        context.create_context()
        settings = context.context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertEquals(settings.get_value('c'), 2)
        settings.update_value('c', value=1)
        settings = context.context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertEquals(settings.get_value('c'), 1)
        settings = ContextManager(WORK_DIR).context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertEquals(settings.get_value('c'), 2)
        ContextManager(SUB_DIR).context_settings().update_value('c', value=1, cascade=True)
        settings = ContextManager(WORK_DIR).context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertEquals(settings.get_value('c'), 1)
        settings = ContextManager('.').context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 2)
        self.assertIsNone(settings.get_value('c'))
        ContextManager(SUB_DIR).context_settings().update_value('c', value=None, cascade=True)
        settings = ContextManager(SUB_DIR).context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertIsNone(settings.get_value('c'))
        settings = ContextManager(WORK_DIR).context_settings()
        self.assertEquals(settings.get_value('a'), 1)
        self.assertEquals(settings.get_value('b'), 1)
        self.assertIsNone(settings.get_value('c'))


if __name__ == '__main__':
    unittest.main()
