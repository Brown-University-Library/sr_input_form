"""
Checks the guarded test runner's automated-authorization behavior.
"""

import os
from contextlib import redirect_stderr
from io import StringIO
from unittest import mock

from django.test import SimpleTestCase

import run_tests as test_runner


class AutomatedTestAuthorizationTest(SimpleTestCase):
    """
    Checks automated and manual authorization paths.
    """

    def test_exact_automated_authorization_is_accepted(self):
        """
        Checks that the exact automated authorization bypasses the terminal prompt.
        """
        warning = 'database warning\n'
        error_output = StringIO()
        with redirect_stderr(error_output), mock.patch.object(test_runner, 'request_confirmation') as request_confirmation:
            is_authorized = test_runner.request_test_run_authorization(
                warning,
                test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE,
            )

        self.assertTrue(is_authorized)
        request_confirmation.assert_not_called()
        self.assertIn(warning, error_output.getvalue())
        self.assertIn(test_runner.AUTOMATED_TEST_AUTHORIZATION_ENVIRONMENT_KEY, error_output.getvalue())

    def test_incorrect_automated_authorization_uses_manual_confirmation(self):
        """
        Checks that any other authorization value retains the manual prompt.
        """
        warning = 'database warning\n'
        with mock.patch.object(test_runner, 'request_confirmation', return_value=True) as request_confirmation:
            is_authorized = test_runner.request_test_run_authorization(warning, 'incorrect-value')

        self.assertTrue(is_authorized)
        request_confirmation.assert_called_once_with(warning)

    @mock.patch.object(test_runner, 'run_django_tests')
    @mock.patch.object(test_runner, 'load_runtime_environment')
    @mock.patch.object(test_runner.socket, 'gethostname', return_value='prdisa')
    def test_production_hostname_blocks_automated_authorization(
        self,
        gethostname,
        load_runtime_environment,
        run_django_tests,
    ):
        """
        Checks that automated authorization cannot override the production-hostname refusal.
        """
        exit_code = test_runner.manage_test_run([], test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE)

        self.assertEqual(1, exit_code)
        gethostname.assert_called_once_with()
        load_runtime_environment.assert_not_called()
        run_django_tests.assert_not_called()

    @mock.patch.object(test_runner, 'run_django_tests', return_value=0)
    @mock.patch.object(test_runner, 'request_test_run_authorization', return_value=True)
    @mock.patch.object(test_runner, 'build_database_warning', return_value='database warning\n')
    @mock.patch.object(test_runner, 'load_runtime_environment')
    @mock.patch.object(test_runner.socket, 'gethostname', return_value='dlibwwwcit')
    def test_automated_authorization_runs_tests_on_nonproduction_hostname(
        self,
        gethostname,
        load_runtime_environment,
        build_database_warning,
        request_test_run_authorization,
        run_django_tests,
    ):
        """
        Checks that exact authorization runs tests on a non-production hostname.
        """
        warning = 'database warning\n'
        test_labels = ['disa_app.tests.test_renamer']
        exit_code = test_runner.manage_test_run(test_labels, test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE)

        self.assertEqual(0, exit_code)
        gethostname.assert_called_once_with()
        load_runtime_environment.assert_called_once_with()
        build_database_warning.assert_called_once_with()
        request_test_run_authorization.assert_called_once_with(warning, test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE)
        run_django_tests.assert_called_once_with(test_labels)

    @mock.patch.object(test_runner, 'manage_test_run', return_value=0)
    @mock.patch.object(test_runner, 'parse_arguments')
    def test_main_reads_authorization_from_startup_environment(self, parse_arguments, manage_test_run):
        """
        Checks that main passes startup-environment authorization to the guarded runner.
        """
        parse_arguments.return_value.test_labels = []
        environment = {
            test_runner.AUTOMATED_TEST_AUTHORIZATION_ENVIRONMENT_KEY: test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE,
        }
        with mock.patch.dict(os.environ, environment, clear=False), self.assertRaises(SystemExit) as system_exit:
            test_runner.main()

        self.assertEqual(0, system_exit.exception.code)
        manage_test_run.assert_called_once_with([], test_runner.AUTOMATED_TEST_AUTHORIZATION_VALUE)
