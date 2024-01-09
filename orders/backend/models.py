from django.contrib.auth.base_user import BaseUserManager
from django.contrib.auth.models import AbstractUser
from django.db import models


ORDER_STATUS = (
    ("1", "New"),
    ("2", "In progress"),
    ("3", "Delivery"),
    ("4", "Completed"),
    ("5", "Rejected"),
)


class UserManager(BaseUserManager):
    use_in_migrations = True

    def _create_user(self, email, password, **extra_fields):
        if not email:
            raise ValueError('The given email must be set')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        return self._create_user(email, password, **extra_fields)

    def create_superuser(self, email, password, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superuser must have is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superuser must have is_superuser=True.')

        return self._create_user(email, password, **extra_fields)


class User(AbstractUser):
    USERNAME_FIELD = "email"
    EMAIL_FIELD = "email"
    REQUIRED_FIELDS = []
    objects = UserManager()

    email = models.EmailField(unique=True)
    company = models.CharField(max_length=100)
    position = models.CharField(max_length=100)

    def __str__(self):
        return f'{self.first_name} {self.last_name}'

    class Meta:
        ordering = ('first_name', 'last_name', )


class Shop(models.Model):
    name = models.CharField(max_length=100)
    url = models.URLField(max_length=400, null=True)

    class Meta:
        verbose_name = 'Shop'

    def __str__(self):
        return self.name


class Category(models.Model):
    name = models.CharField(max_length=100)
    shops = models.ManyToManyField(Shop, related_name='categories', through='ShopCategory')

    class Meta:
        verbose_name = 'Category'

    def __str__(self):
        return self.name


class ShopCategory(models.Model):
    shop = models.ForeignKey(Shop, related_name='shops', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, related_name='categories', on_delete=models.CASCADE)


class Product(models.Model):
    name = models.CharField(max_length=100)
    category = models.ForeignKey(Category, related_name='products', on_delete=models.CASCADE)

    class Meta:
        verbose_name = 'Product'

    def __str__(self):
        return self.name


class ProductInfo(models.Model):
    name = models.CharField(max_length=100)
    product = models.ForeignKey(Category, related_name='product', on_delete=models.CASCADE)
    shop = models.ForeignKey(Category, related_name='shop', on_delete=models.CASCADE)
    quantity = models.IntegerField()
    price = models.PositiveIntegerField()
    price_rrc = models.PositiveIntegerField()

    class Meta:
        verbose_name = 'ProductInfo'

    def __str__(self):
        return self.name


class Parameter(models.Model):
    name = models.CharField(max_length=100)

    class Meta:
        verbose_name = 'Parameter'

    def __str__(self):
        return self.name


class ProductParameter(models.Model):
    product_info = models.ForeignKey(ProductInfo, related_name='product_info', on_delete=models.CASCADE)
    parameter = models.ForeignKey(Parameter, related_name='parameters', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)


class Order(models.Model):
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    dt = models.DateTimeField(auto_now_add=True)
    status = models.CharField(choices=ORDER_STATUS)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name='orders', on_delete=models.CASCADE)
    product = models.ForeignKey(Product, related_name='products', on_delete=models.CASCADE)
    shop = models.ForeignKey(Shop, related_name='shops', on_delete=models.CASCADE)
    quantity = models.PositiveIntegerField()


class Contact(models.Model):
    user = models.ForeignKey(User, related_name='orders', on_delete=models.CASCADE)
    value = models.CharField(max_length=100)
    type = models.CharField(max_length=100)