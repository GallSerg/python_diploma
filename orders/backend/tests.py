import json

from dotenv import load_dotenv
from django.test import TestCase, RequestFactory
from rest_framework.test import APIRequestFactory
from .serializers import ContactSerializer, AddressSerializer
from .models import User, Contact, Shop, ProductInfo, Category, Product, ShopCategory
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
        print(f'Test1: Compare string \'{response.data['Comment']}\' from response with '
              f'string \'User john@example.com is created\'')
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data['Comment'], 'User john@example.com is created')

    def test_get_user_after_creation(self):
        """
        Test the retrieval of a user by sending a GET request with a valid token and checking the response status code and data.
        """
        data = {
            'first_name': 'John',
            'last_name': 'Doe',
            'email': 'john@example.com',
            'password': 'password123',
            'company': 'Example Company',
            'position': 'Developer'
        }
        user = User.objects.create(**data)
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.get(path='/api/v1/user/details', headers=headers, format='json')
        print(f'Test2: Compare status {response.status_code} from response with status 200')
        print(f'Test2: Compare id \'{response.data["id"]}\' from response with id {user.id}')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data["id"], user.id)


class ContactViewTests(APITestCase):

    url = '/api/v1/user/contact'

    def test_get_method(self):
        user = User.objects.create(email='tgm@example.com')
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
        user = User.objects.create(email='tpma@example.com')
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


class PartnerStateTests(APITestCase):

    url = '/api/v1/partner/state'

    def test_authenticated_user(self):
        user = User.objects.create(email='test2@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        shop = Shop.objects.create(user=user, name='Test Shop', state=True)
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test6: Compare status {response.status_code} from response with status 200')
        self.assertEqual(response.status_code, 200)

    def test_non_partner_user(self):
        user = User.objects.create(email='test2@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        user.type = 'customer'
        user.save()
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test7: Compare status {response.status_code} from response with status 403')
        self.assertEqual(response.status_code, 403)

    def test_shop_state_on(self):
        user = User.objects.create(email='test2@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        shop = Shop.objects.create(user=user, name='Test Shop', state=True)
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test8: Compare status {response.status_code} from response with status 200')
        print(f'Test8: Compare string \'{response.data}\' from response with'
              f' the correct structure Name: \"Test Shop\" and State on')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'Name': 'Test Shop', 'State': 'on'})

    def test_shop_state_off(self):
        user = User.objects.create(email='test2@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        shop = Shop.objects.create(user=user, name='Test Shop', state=False)
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test9: Compare status {response.status_code} from response with status 200')
        print(f'Test9: Compare string \'{response.data}\' from response with'
              f' the correct structure Name: \"Test Shop\" and State off')
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data, {'Name': 'Test Shop', 'State': 'off'})


class TestMyView(APITestCase):

    url = '/api/v1/basket'

    def test_authenticated_user(self):
        user = User.objects.create(email='test3@example.com', first_name='Test', last_name='User')
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test10: Compare status {response.status_code} from response with status 200')
        self.assertEqual(response.status_code, 200)

    def test_unauthenticated_user(self):
        user = User.objects.create(email='test3@example.com', first_name='Test', last_name='User')
        token = Token.objects.create(user=user)
        headers = {'Authorization': 'bad token'}
        response = self.client.get(path=self.url, headers=headers, format='json')
        print(f'Test11: Compare status {response.status_code} from response with status 401')
        self.assertEqual(response.status_code, 401)

    def test_items_added_successfully(self):
        user = User.objects.create(email='test3@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        shop = Shop.objects.create(id=1000, user=user, name='Test Shop')
        category = Category.objects.create(id=500, name='Test category')
        sc = ShopCategory.objects.create(shop=shop, category=category)
        product = Product.objects.create(name='Test product', category=category)
        product_info = ProductInfo.objects.create(name='Test pi',
                                                  product=product,
                                                  shop=shop,
                                                  external_id=1,
                                                  quantity=1,
                                                  price=10000,
                                                  price_rrc=8000
                                                  )
        data = {'items': json.dumps([{
            "product_info": 1,
            "quantity": 5
        }])}
        response = self.client.post(path=self.url, headers=headers, data=data, format='json')
        print(f'Test12: Compare status {response.status_code} from response with status 201')
        self.assertEqual(response.status_code, 201)

    def test_non_new_state_basket(self):
        user = User.objects.create(email='test3@example.com', first_name='Test', last_name='User', type='partner')
        token = Token.objects.create(user=user)
        headers = {'Authorization': f'Token {token.key}'}
        data = {}  # Missing 'items' key
        response = self.client.post(path=self.url, headers=headers, data=data, format='json')
        print(f'Test13: Compare status {response.status_code} from response with status 400')
        self.assertEqual(response.status_code, 400)
