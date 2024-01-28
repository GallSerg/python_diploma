from rest_framework import serializers
from .models import (User, Shop, ShopCategory, Order, OrderItem, Category, Contact,
                     ConfirmToken, Address, Product, ProductInfo, ProductParameter, Parameter)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', )


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('id', 'name',)


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('name', 'category',)


class ProductInfoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ('id', 'name', 'product', 'shop', 'quantity', 'price', 'price_rrc',)


class ParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = Parameter
        fields = ('name',)


class ProductParameterSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductParameter
        fields = ('product_info', 'parameter', 'value',)


class OrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'status',)


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product', 'shop', 'quantity',)


class AddressSerializer(serializers.ModelSerializer):
    class Meta:
        model = Address
        fields = ('id', 'city', 'street', 'house', 'structure', 'building', 'apartment', 'contact')


class ContactSerializer(serializers.ModelSerializer):
    address = AddressSerializer(read_only=True, many=True)

    class Meta:
        model = Contact
        fields = ('id', 'user', 'phone', 'address')
        read_only_fields = ('address',)
