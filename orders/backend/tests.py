from django.test import TestCase
from rest_framework.test import APIRequestFactory
from .views import UserRegister
from rest_framework.test import APITestCase

factory = APIRequestFactory()
view = UserRegister.as_view()


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
        request = factory.post('api/v1/user/register/', data, format='json')
        response = view(request)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['Comment'], 'User john@example.com is created')


class ContactViewTests(APITestCase):
    def test_get_method(self):
        response = self.client.get('api/v1/user/contact/')
        self.assertEqual(response.status_code, 200)

    def test_post_method_authenticated(self):
        # Assume user is authenticated
        self.client.force_authenticate(user=self.user)
        data = {'city': 'New York', 'street': 'Broadway', 'phone': '1234567890'}
        response = self.client.post('api/v1/user/contact/', data, format='json')
        self.assertEqual(response.status_code, 201)

    def test_post_method_not_authenticated(self):
        # Assume user is not authenticated
        data = {'city': 'New York', 'street': 'Broadway', 'phone': '1234567890'}
        response = self.client.post('api/v1/user/contact/', data, format='json')
        self.assertEqual(response.status_code, 401)
