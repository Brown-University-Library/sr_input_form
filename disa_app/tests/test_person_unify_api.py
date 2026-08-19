# -*- coding: utf-8 -*-

import json
import logging
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase
from django.urls import reverse


log = logging.getLogger(__name__)


class PersonUnifyApiTest(TestCase):
    """Checks the person-link-referents API endpoint."""

    def test_post_links_referents_and_uses_authenticated_user_as_by_value(self):
        user = User.objects.create_user(username='researcher', password='pw')
        self.client.force_login(user)

        payload = {
            'referent_uuid_1': '11111111111111111111111111111111',
            'referent_uuid_2': '22222222222222222222222222222222',
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
