import os
import unittest
from unittest.mock import Mock

from dotenv import load_dotenv
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory
from .serializers import ContactSerializer, AddressSerializer
from .models import User, Contact, Shop
from .views import UserRegister, PartnerState
from rest_framework.test import APITestCase
from rest_framework.authtoken.models import Token


load_dotenv()

factory = APIRequestFactory()


class UserCreationTest(TestCase):
    def test_user_creation(self):
        """
        Test the creation of a user by sending a POST request with user data and checking the response status code and data.
        """
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'company': 'Example Company',
            'position': 'Developer'
        }
        request = factory.post(path='/api/v1/user/register/', data=data, format='json')
        response = UserRegister.as_view()(request=request, backend=None)
        print(f'Test1: Compare status {response.status_code} from response with status 201')
        print(f'Test2: Compare string \'{response.data['Comment']}\' from response with '
              f'string \'User john@example.com is created\'')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['Comment'], 'User john@example.com is created')


class ContactViewTests(APITestCase):
    url = '/api/v1/user/contact'

    def test_get_method(self):
        user = User.objects.create(email='john@example.com')
        contact_data = {
            'city': 'New York',
            'street': 'Broadway',
            'house': '44',
            'structure': '23',
            'building': 'C1',
            'apartment': '11',
            'phone': '811111111111',
            'user': user,
        }
        token = Token.objects.create(user=user)
        contact_id = Contact.objects.create(phone=contact_data['phone'], user=user)
        adr_serializer = AddressSerializer(data=contact_data, partial=True)
        if adr_serializer.is_valid():
            adr_serializer.save(contact=contact_id)
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test3: Compare status {response.status_code} from response with status 200')
        self.assertEqual(response.status_code, 200)

    def test_post_method_authenticated(self):
        # Assume user is authenticated
        user = User.objects.create(email='john@example.com')
        contact_data = {
            'city': 'New York',
            'street': 'Broadway',
            'house': '44',
            'structure': '23',
            'building': 'C1',
            'apartment': '11',
            'phone': '811111111191',
            'user': user.id
        }
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.post(path=self.url, headers=headers, data=contact_data, format='json')
        print(f'Test4: Compare status {response.status_code} from response with status 201')
        self.assertEqual(response.status_code, 201)

    def test_post_method_not_authenticated(self):
        # Assume user is not authenticated
        headers = {'Authorization': 'Bad token'}
        data = {'city': 'New York', 'street': 'Broadway', 'phone': '1234567890'}
        response = self.client.post(path=self.url, headers=headers, data=data, format='json')
        print(f'Test5: Compare status {response.status_code} from response with status 401')
        self.assertEqual(response.status_code, 401)


class TestPartnerState(unittest.TestCase):
    user = User.objects.create(email='test@example.com', first_name='Test', last_name='User', type='partner')
    token = Token.objects.create(user=user)

    def setUp(self):
        self.factory = RequestFactory()

    def test_authenticated_user(self):
        request = self.factory.get('/')
        request.user = self.user
        request.META['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        response = PartnerState.as_view()(request)
        self.assertEqual(response.status_code, 200)

    def test_non_partner_user(self):
        self.user.type = 'customer'
        self.user.save()
        request = self.factory.get('/')
        request.user = self.user
        request.META['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        response = PartnerState.as_view()(request)
        self.assertEqual(response.status_code, 403)

    def test_shop_state_on(self):
        request = self.factory.get('/')
        request.user = self.user
        request.META['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        shop = Shop.objects.create(user=self.user, name='Test Shop', state=True)
        response = PartnerState.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'Name': 'Test Shop', 'State': 'on'})

    def test_shop_state_off(self):
        request = self.factory.get('/')
        request.user = self.user
        request.META['HTTP_AUTHORIZATION'] = f'Token {self.token.key}'
        shop = Shop.objects.create(user=self.user, name='Test Shop', state=False)
        response = PartnerState.as_view()(request)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'Name': 'Test Shop', 'State': 'off'})
