import json
from django.db.models import Q
from rest_framework.throttling import UserRateThrottle
from drf_spectacular.utils import extend_schema, OpenApiExample, OpenApiParameter
from rest_framework.generics import ListAPIView
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.request import Request
from yaml import load as load_yaml, Loader
from requests import get
from .models import (User, Shop, ShopCategory, Order, OrderItem, Category, Contact, Address,
                     ConfirmToken, Product, ProductInfo, ProductParameter, Parameter, UserProfile)
from .serializers import (UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer,
                          ContactSerializer, ProductSerializer, ProductInfoSerializer, ProductParameterSerializer,
                          ParameterSerializer, AddressSerializer, ConfirmTokenSerializer, UserLoginSerializer)
from .signals import new_user_registered, new_order, social_auth_user
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token
from django.shortcuts import render


def custom_login_view(request):
    """
    Function to register through Google OAuth2.
    Args:
        request: The HTTP request object.
    Returns:
        A rendered HTTP response for the register through Google OAuth2.
    """
    return render(request, 'social/login.html')


def profile_view(request):
    """
    This function gets the user and returns a rendered profile.html page with the user's profile information.
    """
    if not request.user.is_authenticated:
        return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
    user_profile = UserProfile.objects.get_or_create(user=request.user)
    return render(request, 'profile.html', {
        'user_profile': user_profile,
        'user': user_profile[0].user,
        'avatar': user_profile[0].avatar
    })


class UserRegister(APIView):
    """
    View to register User in the System
    """
    @extend_schema(
        request=UserSerializer,
        responses={
            201: {'example': {'Status': True, 'Comment': 'User created'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Process a POST request and create a new user.

        Args:
            request, backend for social authentication

        Returns:
            The response contains the status of the user register, comment and errors.
        """
        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', }.issubset(request.data):
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered.send(sender=User, user_id=user.id)
                return Response({'Status': True, 'Comment': f'User {user.email} is created'}, status=201)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': user_serializer.errors}, status=400)

        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class EmailConfirm(APIView):
    """
    View to confirm user's token
    """
    @extend_schema(
        request=ConfirmTokenSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Token is correct'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Token is incorrect'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Confirms user token (sent by email)

        Args:
            request

        Returns:
            The response contains the status of the user token confirmation, comment and errors.
        """
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmToken.objects.filter(user__email=request.data['email'],
                                                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'Status': True, 'Comment': 'Token is correct'}, status=200)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Token is incorrect'}, status=400)

        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Not confirmed'}, status=400)


class UserLogin(APIView):
    """
    View to sign in user into the system
    """
    @extend_schema(
        request=UserLoginSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Logged in correctly', 'Token': 'token value'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Log in user by username and password

        Args:
            request

        Returns:
            The response contains the status of the user token confirmation, comment and errors.
        """
        if {'username', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['username'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, i = Token.objects.get_or_create(user=user)

                    return Response({'Status': True, 'Comment': 'Logged in correctly', 'Token': token.key})

            return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Can not authorise'}, status=403)

        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class ContactView(APIView):
    """
    View to work with the contact: create, read, update and delete
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            200: {'example': {
                "id": 1,
                "user": 2,
                "phone": "+79998887777",
                "address": [
                    {
                        "id": 1,
                        "city": "Perm",
                        "street": "Belinskogo",
                        "house": "31",
                        "structure": "1",
                        "building": "1",
                        "apartment": "101",
                        "contact": 1
                    }
                ],
            }
            },
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Contact not found'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get contacts and address by current user

        Args:
            request

        Returns:
            The response contains the contacts and addresses of the current user (search by token), comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        contact = Contact.objects.filter(user_id=request.user.id)
        if contact:
            serializer = ContactSerializer(contact, many=True)
            return Response(serializer.data)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Contact not found'}, status=400)

    @extend_schema(
        request=ContactSerializer,
        responses={
            201: {'example': {'Status': True, 'Comment': 'New contact with address created'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create contact (if the system gets new phone number) and addresses to current user

        Args:
            request

        Returns:
            The response contains the contact creating information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)

        if {'city', 'street', 'phone'}.issubset(request.data):
            contact_serializer = ContactSerializer(data=request.data)
            adr_serializer = AddressSerializer(data=request.data)
            if contact_serializer.is_valid():
                if adr_serializer.is_valid():
                    contact_id = Contact.objects.filter(phone=(request.data['phone'])).first()
                    if contact_id:
                        adr_serializer.save(contact=contact_id)
                        return Response({'Status': True, 'Comment': f'New address created for {request.data['phone']}'}, status=201)
                    else:
                        contact_serializer.save()
                        contact_id = Contact.objects.filter(phone=(request.data['phone'])).first()
                        adr_serializer.save(contact=contact_id)
                        return Response({'Status': True, 'Comment': 'New contact with address created'}, status=201)
                else:
                    return Response({'Status': False, 'Comment': 'Error', 'Errors': adr_serializer.errors}, status=400)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': contact_serializer.errors}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Deleted {count} contacts and {count} addresses'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete current user's contacts by id in request

        Args:
            request

        Returns:
            The response contains the deleted contacts count and deleted addresses count of the current user
            (search by token), comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)

        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.strip().split(',')
            contact_query = Q()
            adr_query = Q()
            objects_deleted = False
            for contact_id in items_list:
                if contact_id.isdigit():
                    contact_query = contact_query | Q(user_id=request.user.id, id=contact_id)
                    adr_query = adr_query | Q(contact=contact_id)
                    objects_deleted = True
                else:
                    return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Id must be integer'}, status=400)
            if objects_deleted:
                deleted_adr = Address.objects.filter(adr_query).delete()[0]
                deleted_count = Contact.objects.filter(contact_query).delete()[0]
                return Response({'Status': True,
                                 'Comment': f'Deleted {deleted_count} contacts and {deleted_adr} addresses'})
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Contact ids not found'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Contact edited'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Update contact (search by phone) of the current user

        Args:
            request

        Returns:
            The response contains the contact edit information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if 'id' in request.data:
            if request.data['id'].isdigit():
                contact = Contact.objects.filter(id=request.data['id'], user_id=request.user.id).first()
                if contact:
                    contact_serializer = ContactSerializer(contact, data=request.data, partial=True)
                    adr_serializer = AddressSerializer(data=request.data)
                    if contact_serializer.is_valid():
                        if adr_serializer.is_valid():
                            contact_serializer.save()
                            adr_serializer.save(contact=contact)
                            return Response({'Status': True, 'Comment': 'Contact edited, address added'})
                        else:
                            return Response({'Status': False,
                                             'Comment': 'Error', 'Errors': adr_serializer.errors}, status=400)
                    else:
                        return Response({'Status': False,
                                         'Comment': 'Error', 'Errors': contact_serializer.errors}, status=400)
                else:
                    return Response({'Status': False,
                                     'Comment': 'Error', 'Errors': 'Contact id is not found in database'}, status=400)
            else:
                return Response({'Status': False,
                                 'Comment': 'Error', 'Errors': 'Incorrect id'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Id is not found in request'}, status=400)


class UserDetails(APIView):
    """
    View to get and edit User
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=UserSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'User created'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
        }
    )
    def get(self, request: Request, *args, **kwargs):
        """
        Get current user (by token)

        Args:
            request

        Returns:
            The response contains the user information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Edited'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Serializer errors'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Edits current user (by token)

        Args:
            request

        Returns:
            The response contains the user edit information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        else:
            request.user.set_password(request.data['password'])
        user_serializer = UserSerializer(request.user, data=request.data, partial=True)
        if user_serializer.is_valid():
            user_serializer.save()
            return Response({'Status': True, 'Comment': 'Edited'}, status=200)
        else:
            return Response({'Status': False, 'Comment': 'Error', 'Errors': user_serializer.errors}, status=400)


class CategoryView(ListAPIView):
    """
    View to get categories
    """
    throttle_classes = [UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    """
    View to get shops
    """
    throttle_classes = [UserRateThrottle]
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    """
    View to edit Partner's goods data
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            200: {'example': {'Status': True, 'Comment': 'Partner updated'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Load data from yaml-file with partner data. Also check if the current user is a partner.

        Args:
            request

        Returns:
            The response contains the partner edit information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        user_type = User.objects.filter(id=request.user.id).values('type')
        if user_type[0]['type'] != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        url = request.data.get('url')
        if url:
            stream = get(url).content
            data = load_yaml(stream, Loader=Loader)
            shop, i = Shop.objects.get_or_create(name=data['shop'], url=url, user_id=request.user.id)
            for category in data['categories']:
                category_object, i = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, i = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          name=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, i = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return Response({'Status': True, 'Comment': 'Partner updated'})
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class PartnerState(APIView):
    """
    View to get and change partner's state
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        responses={
            201: {'example': {'Name': 'Shop name', 'State': 'Some state'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get partner's state

        Args:
            request

        Returns:
            The response contains the partner's state, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        shop = Shop.objects.filter(user_id=request.user.id)[0]
        st = 'on' if shop.state else 'off'
        return Response({'Name': shop.name, 'State': st}, status=200)

    @extend_schema(
        responses={
            200: {'example': {'Status': True, 'Comment': 'Partner\'s state updated'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Edit partner's state

        Args:
            request

        Returns:
            The response contains the partner's state edit information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        state = request.data.get('state')
        if state:
            if state in ['on', 'off']:
                state = True if state == 'on' else False
                Shop.objects.filter(user_id=request.user.id).update(state=state)
                return Response({'Status': True, 'Comment': 'Partner\'s state updated'})
            else:
                return Response({'Status': False, 'Errors': 'State field is incorrect'}, status=400)
        return Response({'Status': False, 'Errors': 'Bad request'}, status=400)


class PartnerOrders(APIView):
    """
    View to get partner's orders
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=OrderSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Order serializer data'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get orders of current partner (= current user)

        Args:
            request

        Returns:
            The response contains the orders' information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class OrderView(APIView):
    """
    View to get and edit order information
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=OrderSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Order serializer data'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get order of current user

        Args:
            request

        Returns:
            The response contains the order information (including products), comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    @extend_schema(
        request=OrderSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Order in progress'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Edit order's state of current user and send a notification

        Args:
            request

        Returns:
            The response contains the order's state update information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if {'id', 'contact'}.issubset(request.data):
            if request.data['id'].isdigit():
                order = Order.objects.filter(user_id=request.user.id, id=request.data['id'])
                if order:
                    is_updated = (Order.objects.filter(user_id=request.user.id, id=request.data['id'])
                                  .update(state='in_progress'))
                    if is_updated:
                        new_order.send(sender=self.__class__, user_id=request.user.id)
                        return Response({'Status': True, 'Comment': 'Order in progress'})
                else:
                    Response({'Status': False, 'Comment': 'Error', 'Errors': 'Order is not found'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class BasketView(APIView):
    """
    View to manage cart: create, read, update, delete
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=OrderSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Order serializer data'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request, *args, **kwargs):
        """
        Get cart (in state new) of current user

        Args:
            request

        Returns:
            The response contains the cart information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        basket = Order.objects.filter(user_id=request.user.id, state='new')
        serializer = OrderSerializer(basket, many=True)
        if serializer:
            return Response(serializer.data, status=200)
        return Response({'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}, status=401)

    @extend_schema(
        request=OrderSerializer,
        responses={
            201: {'example': {'Status': True, 'Comment': 'Items created'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def post(self, request, *args, **kwargs):
        """
        Create a new cart of current user or add items in existing cart (cart in state new)

        Args:
            request

        Returns:
            The response contains the cart edit information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_dict = json.loads(items_sting)
            basket, i = Order.objects.get_or_create(user_id=request.user.id, state='new')
            total_sum = 0
            objects_created = 0
            for order_item in items_dict:
                order_item.update({'order': basket.id})
                pi = ProductInfo.objects.filter(id=order_item["product_info"])[0]
                total_sum += pi.price * order_item["quantity"]
                serializer = OrderItemSerializer(data=order_item)
                if serializer.is_valid():
                    serializer.save()
                    objects_created += 1
                else:
                    return Response({'Status': False, 'Comment': f'Error in item. {objects_created} objects created',
                                     'Errors': serializer.errors}, status=400)
            ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
            return Response({'Status': True, 'Comment': f'{objects_created} objects are created'}, status=201)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Items deleted'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def delete(self, request, *args, **kwargs):
        """
        Delete current user cart

        Args:
            request

        Returns:
            The response contains the cart deleting information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_list = items_sting.split(',')
            basket = Order.objects.filter(user_id=request.user.id, state='new')[0]
            query = Q()
            objects_deleted = False
            for order_item_id in items_list:
                if order_item_id.isdigit():
                    query = query | Q(order_id=basket.id, id=int(order_item_id))
                    objects_deleted = True
            if objects_deleted:
                deleted_count = OrderItem.objects.filter(query).delete()[0]
                order_items = OrderItem.objects.filter(order=basket.id)
                total_sum = 0
                for pib in order_items:
                    pi = ProductInfo.objects.filter(id=pib.product_info_id)[0]
                    total_sum += pi.price * pib.quantity
                ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
                return Response({'Status': True, 'Comment': f'{deleted_count} deleted'}, status=200)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Items are not found'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)

    @extend_schema(
        request=ContactSerializer,
        responses={
            200: {'example': {'Status': True, 'Comment': 'Items edited'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def put(self, request, *args, **kwargs):
        """
        Add items into the cart

        Args:
            request

        Returns:
            The response contains the cart updating information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        items_sting = request.data.get('items')
        if items_sting:
            items_dict = json.loads(items_sting)
            basket = Order.objects.filter(user_id=request.user.id, state='new')[0]
            if basket:
                objects_updated = 0
                for order_item in items_dict:
                    if isinstance(order_item['id'], int) and isinstance(order_item['quantity'], int):
                        objects_updated += OrderItem.objects.filter(order_id=basket.id, id=order_item['id']).update(
                            quantity=order_item['quantity'])
                    else:
                        return Response({'Status': False, 'Comment': f'Error in item. {objects_updated} updated',
                                         'Errors': f'Incorrect value in item {order_item}'}, status=400)
                order_items = OrderItem.objects.filter(order=basket.id)
                total_sum = 0
                for pib in order_items:
                    pi = ProductInfo.objects.filter(id=pib.product_info_id)[0]
                    total_sum += pi.price * pib.quantity
                ts = Order.objects.filter(id=basket.id).update(total_sum=total_sum)
                return Response({'Status': True, 'Comment': f'{objects_updated} updated'}, status=200)
            else:
                Response({'Status': False, 'Comment': 'Error', 'Errors': 'Basket is not found'}, status=400)
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class ProductInfoView(APIView):
    """
    View to get product info with filter parameters (shop and category)
    """
    throttle_classes = [UserRateThrottle]

    @extend_schema(
        request=ProductInfoSerializer,
        responses={
            201: {'example': {'Status': True, 'Comment': 'Product info'}},
            400: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}},
            401: {'example': {'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}},
        }
    )
    def get(self, request: Request, *args, **kwargs):
        """
        Get information of product filtering by parameters (shop and category)

        Args:
            request

        Returns:
            The response contains the product information, comment and errors.
        """
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        query = Q(shop__state=True)
        shop_id = request.query_params.get('shop_id')
        category_id = request.query_params.get('category_id')
        if shop_id:
            query = query & Q(shop_id=shop_id)
        if category_id:
            query = query & Q(product__category_id=category_id)
        queryset = ProductInfo.objects.filter(query)
        serializer = ProductInfoSerializer(queryset, many=True)
        return Response(serializer.data, status=200)
