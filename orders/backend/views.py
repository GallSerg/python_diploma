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
                     ConfirmToken, Product, ProductInfo, ProductParameter, Parameter)
from .serializers import (UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer,
                          ContactSerializer, ProductSerializer, ProductInfoSerializer, ProductParameterSerializer,
                          ParameterSerializer, AddressSerializer)
from .signals import new_user_registered, new_order
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


class UserRegister(APIView):
    """
    Register User in the System
    """
    @extend_schema(
        parameters=[
            OpenApiParameter(name='last_name', description='Mandatory last_name', required=True, type=str),
            OpenApiParameter(
                name='email',
                location=OpenApiParameter.QUERY,
                description='Mandatory field',
                examples=[
                    OpenApiExample(
                        'Example 1',
                        summary='short optional summary',
                        description='longer description',
                        value='Hello'
                    ),
                ],
            ),
        ],
        examples=[
            OpenApiExample(
                'Example 2',
                description='check description',
                value='check',
            ),
        ],
        responses={200: "OK"},
    )
    def post(self, request, *args, **kwargs):

        if {'first_name', 'last_name', 'email', 'password', 'company', 'position', }.issubset(request.data):
            request.data._mutable = True
            request.data.update({})
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered.send(sender=self.__class__, user_id=user.id)
                return Response({'Status': True, 'Comment': f'User {user.email} is created'}, status=201)
            else:
                return Response({'Status': False, 'Comment': 'Error', 'Errors': user_serializer.errors}, status=400)

        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class EmailConfirm(APIView):
    def post(self, request, *args, **kwargs):
        if {'email', 'token'}.issubset(request.data):
            token = ConfirmToken.objects.filter(user__email=request.data['email'],
                                                key=request.data['token']).first()
            if token:
                token.user.is_active = True
                token.user.save()
                token.delete()
                return Response({'Status': True})
            else:
                return Response({'Status': False, 'Errors': 'Token is incorrect'}, status=400)

        return Response({'Status': False, 'Errors': 'Not confirmed'}, status=400)


class UserLogin(APIView):

    def post(self, request, *args, **kwargs):
        if {'username', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['username'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, i = Token.objects.get_or_create(user=user)

                    return Response({'Status': True, 'Comment': 'Logged in correctly', 'Token': token.key})

            return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Can not authorise'}, status=403)

        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class ContactView(APIView):
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        contact = Contact.objects.filter(user_id=request.user.id)
        serializer = ContactSerializer(contact, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)

        if {'city', 'street', 'phone'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({'user': request.user.id})
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

    def delete(self, request, *args, **kwargs):
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

    def put(self, request, *args, **kwargs):
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
    throttle_classes = [UserRateThrottle]

    def get(self, request: Request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
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
    throttle_classes = [UserRateThrottle]
    queryset = Category.objects.all()
    serializer_class = CategorySerializer


class ShopView(ListAPIView):
    throttle_classes = [UserRateThrottle]
    queryset = Shop.objects.all()
    serializer_class = ShopSerializer


class PartnerUpdate(APIView):
    throttle_classes = [UserRateThrottle]

    def post(self, request, *args, **kwargs):
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

            return Response({'Status': True, 'Comment': 'Partner is updated'})
        return Response({'Status': False, 'Comment': 'Error', 'Errors': 'Bad request'}, status=400)


class PartnerState(APIView):
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        shop = Shop.objects.filter(user_id=request.user.id)[0]
        st = 'on' if shop.state else 'off'
        return Response({'Name': shop.name, 'State': st}, status=200)

    def post(self, request, *args, **kwargs):
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
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        if request.user.type != 'partner':
            return Response({'Status': False, 'Comment': 'Error',
                             'Error': 'Function is available only for partners'}, status=403)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)


class OrderView(APIView):
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        order = Order.objects.filter(user_id=request.user.id)
        serializer = OrderSerializer(order, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
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
    throttle_classes = [UserRateThrottle]

    def get(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Comment': 'Error', 'Error': 'Not authenticated'}, status=401)
        basket = Order.objects.filter(user_id=request.user.id, state='new')
        serializer = OrderSerializer(basket, many=True)
        if serializer:
            return Response(serializer.data, status=200)
        return Response({'Status': False, 'Comment': 'Error', 'Error': 'Bad request'}, status=401)

    def post(self, request, *args, **kwargs):
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

    def delete(self, request, *args, **kwargs):
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

    def put(self, request, *args, **kwargs):
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
    throttle_classes = [UserRateThrottle]

    def get(self, request: Request, *args, **kwargs):
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
