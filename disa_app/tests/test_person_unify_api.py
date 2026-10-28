# -*- coding: utf-8 -*-

import json
import logging
from unittest.mock import MagicMock, patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


log = logging.getLogger(__name__)


class AllPeopleManagerTest(TestCase):
    """Checks the raw-SQL query and its nested response structure."""

    @patch('disa_app.lib.view_data_person_manager.create_engine')
    def test_get_all_people_groups_referents_and_keeps_people_without_referents(self, mock_create_engine):
        cursor = MagicMock()
        cursor.fetchall.return_value = [
            ('person-1', 'referent-1', 'Mary', 'Jones'),
            ('person-1', 'referent-2', '', 'Smith'),
            ('person-2', None, None, None),
        ]
        connection = mock_create_engine.return_value.raw_connection.return_value
        connection.cursor.return_value = cursor

        from disa_app.lib import view_data_person_manager
        result = view_data_person_manager.get_all_people()

        self.assertEqual(
            {
                'people': [
                    {
                        'person_uuid': 'person-1',
                        'referents': [
                            {'referent_uuid': 'referent-1', 'name': 'Mary Jones'},
                            {'referent_uuid': 'referent-2', 'name': 'Smith'},
                        ],
                    },
                    {'person_uuid': 'person-2', 'referents': []},
                ],
            },
            result,
        )
        sql = cursor.execute.call_args.args[0]
        self.assertIn('FROM `1_people`', sql)
        self.assertIn('LEFT JOIN `6_is_person`', sql)
        self.assertIn('LEFT JOIN `5_referents`', sql)
        self.assertIn('LEFT JOIN `6_referent_names`', sql)
        self.assertIn('WHERE people.resolved_person_uuid IS NULL', sql)
        cursor.close.assert_called_once_with()
        connection.close.assert_called_once_with()


class AllPeopleApiTest(TestCase):
    """Checks the all-people API endpoint."""

    @patch('disa_app.views.view_data_person_manager.get_all_people')
    def test_get_returns_people_with_linked_referents(self, mock_get_all_people):
        user = User.objects.create_user(username='researcher', password='pw')
        self.client.force_login(user)
        mock_get_all_people.return_value = {
            'people': [{
                'person_uuid': 'person-1',
                'referents': [{
                    'referent_uuid': 'referent-1',
                    'name': 'Mary Jones',
                }],
            }],
        }

        response = self.client.get(reverse('data_person_all_url'))

        self.assertEqual(200, response.status_code)
        self.assertEqual(mock_get_all_people.return_value, json.loads(response.content))
        mock_get_all_people.assert_called_once_with()


class LinkReferentApiTest(TestCase):
    """Checks the person-link-referents API endpoint."""

    def test_post_links_referents_and_uses_authenticated_user_as_by_value(self):
        user = User.objects.create_user(username='researcher', password='pw')
        self.client.force_login(user)

        payload = {
            'referent_uuids': [
                '11111111111111111111111111111111',
                '22222222222222222222222222222222',
            ],
            'researcher_note': 'These two referents describe the same person.'
        }

        with patch('disa_app.views.view_data_person_manager.link_referents') as mock_link_referents:
            mock_link_referents.return_value = {'person_uuid': '33333333-3333-3333-3333-333333333333'}

            response = self.client.post(
                reverse('data_person_link_referents_url'),
                data=json.dumps(payload),
                content_type='application/json'
            )

        self.assertEqual(200, response.status_code)
        self.assertEqual(
            {'person_uuid': '33333333-3333-3333-3333-333333333333'},
            json.loads(response.content)
        )
        mock_link_referents.assert_called_once_with(
            '11111111111111111111111111111111',
            '22222222222222222222222222222222',
            'researcher',
            'These two referents describe the same person.'
        )
