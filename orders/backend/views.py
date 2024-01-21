from rest_framework.response import Response
from rest_framework.views import APIView
from yaml import load as load_yaml, Loader
from requests import get
from .models import (User, Shop, ShopCategory, Order, OrderItem, Category, Contact,
                     ConfirmToken, Product, ProductInfo, ProductParameter, Parameter)
from .serializers import (UserSerializer, ShopSerializer, OrderSerializer, OrderItemSerializer, CategorySerializer,
                          ContactSerializer, ProductSerializer, ProductInfoSerializer, ProductParameterSerializer,
                          ParameterSerializer)
from .signals import new_user_registered, new_order
from django.contrib.auth import authenticate
from rest_framework.authtoken.models import Token


class UserRegister(APIView):
    def post(self, request, *args, **kwargs):

        if {'first_name', 'last_name', 'email', 'password', 'company', 'position'}.issubset(request.data):
            request.data._mutable = True
            request.data.update({})
            user_serializer = UserSerializer(data=request.data)
            if user_serializer.is_valid():
                user = user_serializer.save()
                user.set_password(request.data['password'])
                user.save()
                new_user_registered.send(sender=self.__class__, user_id=user.id)
                return Response({'Status': True})
            else:
                return Response({'Status': False, 'Errors': user_serializer.errors})

        return Response({'Status': False, 'Errors': 'Bad request'})


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
                return Response({'Status': False, 'Errors': 'Token is incorrect'})

        return Response({'Status': False, 'Errors': 'Not confirmed'})


class UserLogin(APIView):

    def post(self, request, *args, **kwargs):
        if {'username', 'password'}.issubset(request.data):
            user = authenticate(request, username=request.data['username'], password=request.data['password'])

            if user is not None:
                if user.is_active:
                    token, i = Token.objects.get_or_create(user=user)

                    return Response({'Status': True, 'Token': token.key})

            return Response({'Status': False, 'Errors': 'Can not authorise'})

        return Response({'Status': False, 'Errors': 'Bad request'})


class ProviderUpdate(APIView):
    def post(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return Response({'Status': False, 'Error': 'Not authenticated'}, status=403)
        url = request.data.get('url')
        if url:
            stream = get(url).content
            data = load_yaml(stream, Loader=Loader)

            shop, _ = Shop.objects.get_or_create(name=data['shop'], user_id=request.user.id)
            for category in data['categories']:
                category_object, _ = Category.objects.get_or_create(id=category['id'], name=category['name'])
                category_object.shops.add(shop.id)
                category_object.save()
            ProductInfo.objects.filter(shop_id=shop.id).delete()
            for item in data['goods']:
                product, _ = Product.objects.get_or_create(name=item['name'], category_id=item['category'])

                product_info = ProductInfo.objects.create(product_id=product.id,
                                                          external_id=item['id'],
                                                          model=item['model'],
                                                          price=item['price'],
                                                          price_rrc=item['price_rrc'],
                                                          quantity=item['quantity'],
                                                          shop_id=shop.id)
                for name, value in item['parameters'].items():
                    parameter_object, _ = Parameter.objects.get_or_create(name=name)
                    ProductParameter.objects.create(product_info_id=product_info.id,
                                                    parameter_id=parameter_object.id,
                                                    value=value)

            return Response({'Status': True})

        return Response({'Status': False, 'Errors': 'Bad request'})
