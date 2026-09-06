"""
Checks settings loading and browse subprocess selection.
"""

import json
import os
import shutil
import subprocess
import sys
from io import StringIO
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Dict, Optional
from unittest import mock

from django.test import SimpleTestCase
from dotenv import dotenv_values, load_dotenv

from disa_app.lib import generate_browse_data_in_background

ROOT = Path(__file__).resolve().parents[2]


def run_settings(
    sample: Optional[str],
    inherited: Optional[Dict[str, str]] = None,
    test_settings: bool = False,
) -> subprocess.CompletedProcess:
    """
    Load a copied settings module with disposable dotenv values in a fresh process.
    Called by: DotenvSettingsTest
    """
    with TemporaryDirectory(prefix='disa-settings-') as directory:
        outer = Path(directory)
        code = outer / 'code'
        (code / 'config').mkdir(parents=True)
        for name in ('__init__.py', 'settings.py', 'settings_test.py'):
            shutil.copyfile(ROOT / 'config' / name, code / 'config' / name)
        if sample is not None:
            (outer / '.env').write_text(sample)
        environment = {key: value for key, value in os.environ.items() if not key.startswith('DISA_DJ__')}
        environment.pop('PYTHONPATH', None)
        environment.update(inherited or {})
        module = 'config.settings_test' if test_settings else 'config.settings'
        script = (
            f'import {module} as settings; import json, os; '
            'print(json.dumps({"secret": settings.SECRET_KEY, "database": settings.DATABASES, '
            '"url": os.environ["DISA_DJ__DATABASE_URL"], "required": settings.REQUIRED_ENVIRONMENT_KEYS}))'
        )
        result = subprocess.run(
            [sys.executable, '-c', script],
            cwd=code,
            env=environment,
            capture_output=True,
            text=True,
            check=False,
        )
    return result


class DotenvSettingsTest(SimpleTestCase):
    """
    Checks the real settings module without opening either configured database.
    """

    def test_docker_sample_and_precedence(self):
        """
        Checks all required keys, quoted JSON, Docker database paths, and file precedence.
        """
        sample = (ROOT / 'sample_dot_env.txt').read_text()
        result = run_settings(sample, {'DISA_DJ__SECRET_KEY': 'inherited-value'})
        self.assertEqual(0, result.returncode, result.stderr)
        settings = json.loads(result.stdout)
        self.assertEqual('example_secret_key', settings['secret'])
        self.assertEqual('../DBs/dj_disa.sqlite', settings['database']['default']['NAME'])
        self.assertEqual('mysql+pymysql://user:user@db:3306/stolenrelations', settings['url'])
        self.assertEqual(26, len(settings['required']))
        values = dotenv_values(stream=StringIO(sample))
        self.assertFalse(set(settings['required']) - set(values))
        for key, value in values.items():
            if key.endswith('_JSON') or key == 'DISA_DJ__ALLOWED_HOSTS':
                json.loads(value)

    def test_missing_file_cannot_use_old_bypass(self):
        """
        Checks a missing file fails even when the retired bypass flag is inherited.
        """
        result = run_settings(None, {'DISA_DJ__ENV_SETTINGS_PATH': 'retired.sh'})
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Required dotenv file not found:', result.stderr)

    def test_missing_key_names_the_key(self):
        """
        Checks a missing required key produces a useful error.
        """
        sample = (
            (ROOT / 'sample_dot_env.txt')
            .read_text()
            .replace(
                'DISA_DJ__SECRET_KEY="example_secret_key"',
                '',
            )
        )
        result = run_settings(sample)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('Required environment settings are missing: DISA_DJ__SECRET_KEY', result.stderr)

    def test_invalid_json_fails(self):
        """
        Checks invalid JSON is rejected during settings loading.
        """
        sample = (
            (ROOT / 'sample_dot_env.txt')
            .read_text()
            .replace(
                'DISA_DJ__DEBUG_JSON="true"',
                'DISA_DJ__DEBUG_JSON="invalid-json"',
            )
        )
        result = run_settings(sample)
        self.assertNotEqual(0, result.returncode)
        self.assertIn('JSONDecodeError', result.stderr)

    def test_sample_supports_documented_local_sqlite_override(self):
        """
        Checks the shared sample works with the documented local SQLite replacement.
        """
        sample = (
            (ROOT / 'sample_dot_env.txt')
            .read_text()
            .replace(
                'DISA_DJ__DATABASE_URL="mysql+pymysql://user:user@db:3306/stolenrelations"',
                'DISA_DJ__DATABASE_URL="sqlite:///../DBs/DISA.sqlite"',
            )
        )
        result = run_settings(sample)
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual('sqlite:///../DBs/DISA.sqlite', json.loads(result.stdout)['url'])

    def test_fixture_routing_survives_dotenv(self):
        """
        Checks test settings replace both databases after the file loads.
        """
        sample = (ROOT / 'sample_dot_env.txt').read_text()
        result = run_settings(sample, {'DISA_DJ__TEST_SQLALCHEMY_DATABASE_URL': 'sqlite:////tmp/disa-fixture.sqlite'}, True)
        self.assertEqual(0, result.returncode, result.stderr)
        settings = json.loads(result.stdout)
        self.assertEqual(':memory:', settings['database']['default']['NAME'])
        self.assertEqual('sqlite:////tmp/disa-fixture.sqlite', settings['url'])

    def test_empty_quotes_and_interpolation(self):
        """
        Checks pinned dotenv parsing of empty values, literal dollars, hashes, and interpolation.
        """
        sample = "EMPTY=\nQUOTED='value # literal $USD'\nBASE=file\nEXPANDED=${BASE}/path\n"
        with mock.patch.dict(os.environ, {'BASE': 'inherited'}, clear=True):
            load_dotenv(stream=StringIO(sample), override=True)
            self.assertEqual('', os.environ['EMPTY'])
            self.assertEqual('value # literal $USD', os.environ['QUOTED'])
            self.assertEqual('file/path', os.environ['EXPANDED'])


class BrowseInterpreterTest(SimpleTestCase):
    """
    Checks the background child's interpreter.
    """

    def test_child_uses_current_interpreter(self):
        """
        Checks browse generation receives the parent's interpreter path.
        """
        with mock.patch.object(generate_browse_data_in_background.subprocess, 'Popen') as popen:
            generate_browse_data_in_background.main()
        popen.assert_called_once_with([sys.executable, 'disa_app/lib/generate_browse_data.py'])
