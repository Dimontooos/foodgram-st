from rest_framework import serializers
from rest_framework.validators import UniqueValidator
from django.core.validators import RegexValidator
from drf_extra_fields.fields import Base64ImageField
from djoser.serializers import (
    UserCreateSerializer as DjoserUserCreateSerializer,
    UserSerializer as DjoserUserSerializer,
    TokenCreateSerializer as DjoserTokenCreateSerializer,
    SetPasswordSerializer as DjoserSetPasswordSerializer
)
from recipes.models import (
    User,
    Subscription,
    Product,
    Recipe,
    ProductInRecipe,
    Favorite,
    ShoppingCart
)


class UserCreateSerializer(DjoserUserCreateSerializer):
    email = serializers.EmailField(
        validators=[UniqueValidator(queryset=User.objects.all())]
    )
    username = serializers.CharField(
        validators=[
            UniqueValidator(queryset=User.objects.all()),
            RegexValidator(
                regex=r'^[\w.@+-]+\Z',
                message='Введите корректное имя пользователя.'
            )
        ]
    )

    class Meta(DjoserUserCreateSerializer.Meta):
        model = User
        fields = ('email', 'id', 'username',
                  'first_name', 'last_name', 'password')

    def validate_username(self, value):
        if len(value) > 150:
            raise serializers.ValidationError(
                'Имя пользователя не может превышать 150 символов.'
            )
        return value

    def validate_password(self, value):
        if value.strip() != value:
            raise serializers.ValidationError(
                'Пароль не может содержать пробелы в начале или конце.'
            )
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать не менее 8 символов.'
            )
        return value

    def to_representation(self, instance):
        return {
            'email': instance.email,
            'id': instance.id,
            'username': instance.username,
            'first_name': instance.first_name,
            'last_name': instance.last_name
        }


class UserSerializer(DjoserUserSerializer):
    avatar = serializers.ImageField(
        read_only=True,
        allow_null=True,
        use_url=True
    )
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email',
            'id',
            'username',
            'first_name',
            'last_name',
            'avatar',
            'is_subscribed'
        ]
        read_only_fields = fields

    def get_is_subscribed(self, user):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and Subscription.objects.filter(
                    user=request.user,
                    author=user
                ).exists())


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.IntegerField(
        source='recipes.count',
        read_only=True
    )

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['recipes', 'recipes_count']

    def get_recipes(self, user):
        request = self.context.get('request')
        limit = int(request.GET.get('recipes_limit', 10**10))
        queryset = user.recipes.all()[:limit]
        return RecipeMinifiedSerializer(
            queryset,
            many=True,
            context=self.context
        ).data


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField(
        read_only=True,
        use_url=True
    )

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(DjoserSetPasswordSerializer):
    def validate_new_password(self, value):
        if value.strip() != value:
            raise serializers.ValidationError(
                'Пароль не может содержать пробелы в начале или конце.'
            )
        if len(value) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать не менее 8 символов.'
            )
        return value


class ProductSerializer(serializers.ModelSerializer):
    class Meta:
        model = Product
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeCreateSerializer(serializers.Serializer):
    id = serializers.PrimaryKeyRelatedField(
        queryset=Product.objects.all(),
        required=True
    )
    amount = serializers.IntegerField(
        min_value=1,
        required=True
    )


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(
        source='ingredient.id',
        read_only=True
    )
    name = serializers.CharField(
        source='ingredient.name',
        read_only=True
    )
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit',
        read_only=True
    )
    amount = serializers.IntegerField(
        read_only=True
    )

    class Meta:
        model = ProductInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')
        read_only_fields = fields


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = fields

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else ''


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(
        many=True,
        read_only=True,
        source='products'
    )
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = serializers.SerializerMethodField(read_only=True)

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'ingredients',
            'is_favorited',
            'is_in_shopping_cart',
            'name',
            'image',
            'text',
            'cooking_time'
        )
        read_only_fields = fields

    def get_is_favorited(self, recipe):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and Favorite.objects.filter(
                    user=request.user,
                    recipe=recipe
                ).exists())

    def get_is_in_shopping_cart(self, recipe):
        request = self.context.get('request')
        return (request
                and request.user.is_authenticated
                and ShoppingCart.objects.filter(
                    user=request.user,
                    recipe=recipe
                ).exists())

    def get_image(self, obj):
        request = self.context.get('request')
        return request.build_absolute_uri(obj.image.url) if obj.image else ''


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = IngredientInRecipeCreateSerializer(
        many=True,
        write_only=True,
        required=True
    )
    image = Base64ImageField(
        required=True,
        allow_null=False
    )
    name = serializers.CharField(
        max_length=256,
        required=True
    )
    text = serializers.CharField(required=True)
    cooking_time = serializers.IntegerField(
        min_value=1,
        required=True
    )

    class Meta:
        model = Recipe
        fields = ('id', 'ingredients', 'image', 'name', 'text', 'cooking_time')

    def validate(self, data):
        if self.partial:
            missing_fields = []
            for field in ['ingredients', 'image', 'name', 'text',
                          'cooking_time']:
                if field not in self.initial_data:
                    missing_fields.append(field)
            if missing_fields:
                errors = {
                    field: ['Это поле обязательно.']
                    for field in missing_fields
                }
                raise serializers.ValidationError(errors)
        return data

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Поле 'ingredients' обязательно."
            )
        if len(value) == 0:
            raise serializers.ValidationError(
                "Должна быть хотя бы один ингредиент."
            )
        ingredient_ids = {item['id'].id for item in value}
        if len(ingredient_ids) != len(value):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )
        for item in value:
            if not Product.objects.filter(id=item['id'].id).exists():
                raise serializers.ValidationError(
                    f"Ингредиент с id={item['id'].id} не существует."
                )
        return value

    def validate_image(self, value):
        if not value:
            raise serializers.ValidationError(
                "Изображение обязательно и не может быть пустым."
            )
        return value

    def create_ingredients(self, ingredients_data, recipe):
        ProductInRecipe.objects.bulk_create([
            ProductInRecipe(
                recipe=recipe,
                ingredient=item['id'],
                amount=item['amount']
            )
            for item in ingredients_data
        ])

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        recipe = super().create(validated_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        ingredients_data = validated_data.pop('ingredients', None)
        if ingredients_data is not None:
            instance.products.all().delete()
            self.create_ingredients(ingredients_data, instance)
        return super().update(instance, validated_data)


class TokenCreateSerializer(DjoserTokenCreateSerializer):
    def validate(self, attrs):
        possible_email_fields = [
            'username',
            'login',
            'user',
            'userName',
            'emailAddress'
        ]
        for field in possible_email_fields:
            if field in attrs and 'email' not in attrs:
                attrs['email'] = attrs.pop(field)
        if not attrs.get('email'):
            raise serializers.ValidationError(
                {"email": "Это поле обязательно."}
            )
        if not attrs.get('password'):
            raise serializers.ValidationError(
                {"password": "Это поле обязательно."}
            )
        password = attrs.get('password')
        if password.strip() != password:
            raise serializers.ValidationError(
                'Пароль не может содержать пробелы в начале или конце.'
            )
        if len(password) < 8:
            raise serializers.ValidationError(
                'Пароль должен содержать не менее 8 символов.'
            )
        return super().validate(attrs)
