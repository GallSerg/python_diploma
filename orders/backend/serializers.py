from rest_framework import serializers
from .models import (User, Shop, ShopCategory, Order, OrderItem, Category, Contact,
                     ConfirmToken, Address, Product, ProductInfo, ProductParameter, Parameter)


class UserSerializer(serializers.ModelSerializer):

    class Meta:
        model = User
        fields = ('id', 'first_name', 'last_name', 'email', 'company', 'position', 'type',)


class ShopSerializer(serializers.ModelSerializer):
    class Meta:
        model = Shop
        fields = ('id', 'name', 'url', 'user', 'state',)


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


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = ('id', 'order', 'product_info', 'quantity',)


class ProductInfoInOrderSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductInfo
        fields = ('name', 'price', 'price_rrc',)


class OrderItemsInOrderSerializer(serializers.ModelSerializer):
    product_info = ProductInfoInOrderSerializer(read_only=True)

    class Meta:
        model = OrderItem
        fields = ('quantity', 'product_info',)


class OrderSerializer(serializers.ModelSerializer):
    order_item = OrderItemsInOrderSerializer(read_only=True, many=True)

    class Meta:
        model = Order
        fields = ('id', 'user', 'dt', 'state', 'total_sum', 'order_item')


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
