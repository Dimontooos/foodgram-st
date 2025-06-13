from rest_framework import serializers
from django.core.files.base import ContentFile
import base64
import uuid

from users.models import User, Subscription
from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart, ShortLink
)
from djoser.serializers import TokenCreateSerializer as BaseTokenCreateSerializer


class Base64ImageField(serializers.ImageField):
    def to_internal_value(self, data):
        if isinstance(data, str) and data.startswith('data:image'):
            try:
                format, imgstr = data.split(';base64,')
                ext = format.split('/')[-1]
                if ext not in ['jpeg', 'jpg', 'png']:
                    raise serializers.ValidationError(
                        "Поддерживаются только форматы JPEG и PNG."
                    )
                data = ContentFile(
                    base64.b64decode(imgstr),
                    name=f'{uuid.uuid4()}.{ext}'
                )
            except Exception as e:
                raise serializers.ValidationError(
                    f"Некорректные данные изображения: {str(e)}"
                )
        return super().to_internal_value(data)


class CustomUserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = (
            'email', 'username', 'first_name', 'last_name', 'password'
        )
        extra_kwargs = {
            'password': {'write_only': True, 'required': True},
            'username': {'required': True},
            'email': {'required': True},
            'first_name': {'required': True},
            'last_name': {'required': True}
        }

    def validate(self, attrs):
        if User.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError(
                {"email": "Этот email уже зарегистрирован."}
            )
        if User.objects.filter(username=attrs['username']).exists():
            raise serializers.ValidationError(
                {"username": "Этот username уже занят."}
            )
        return attrs

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

    def create(self, validated_data):
        try:
            user = User.objects.create_user(
                email=validated_data['email'],
                username=validated_data['username'],
                password=validated_data['password'],
                first_name=validated_data.get('first_name', ''),
                last_name=validated_data.get('last_name', '')
            )
        except Exception as e:
            raise serializers.ValidationError(
                {'error': f'Ошибка создания пользователя: {str(e)}'}
            )
        return user


class MinimalUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'id', 'username', 'first_name', 'last_name']
        read_only_fields = ['id']


class UserSerializer(serializers.ModelSerializer):
    is_subscribed = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = [
            'email', 'id', 'username', 'first_name',
            'last_name', 'is_subscribed', 'avatar'
        ]
        read_only_fields = ['id', 'is_subscribed', 'avatar']
        extra_kwargs = {
            'avatar': {'read_only': True, 'allow_null': True}
        }

    def get_is_subscribed(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Subscription.objects.filter(
                user=request.user, author=obj
            ).exists()
        return False


class UserWithRecipesSerializer(UserSerializer):
    recipes = serializers.SerializerMethodField()
    recipes_count = serializers.SerializerMethodField()

    class Meta(UserSerializer.Meta):
        fields = UserSerializer.Meta.fields + ['recipes', 'recipes_count']

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')
        queryset = obj.recipes.all()
        if recipes_limit:
            try:
                queryset = queryset[:int(recipes_limit)]
            except ValueError:
                pass
        return RecipeMinifiedSerializer(
            queryset, many=True, context=self.context
        ).data

    def get_recipes_count(self, obj):
        return obj.recipes.count()


class SetAvatarSerializer(serializers.ModelSerializer):
    avatar = Base64ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetAvatarResponseSerializer(serializers.ModelSerializer):
    avatar = serializers.ImageField()

    class Meta:
        model = User
        fields = ('avatar',)


class SetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(required=True)
    current_password = serializers.CharField(required=True)

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


class IngredientSerializer(serializers.ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')
        read_only_fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(serializers.ModelSerializer):
    id = serializers.IntegerField(source='ingredient.id')
    name = serializers.CharField(source='ingredient.name', read_only=True)
    measurement_unit = serializers.CharField(
        source='ingredient.measurement_unit', read_only=True
    )

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'name', 'measurement_unit', 'amount')


class RecipeMinifiedSerializer(serializers.ModelSerializer):
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = ('id', 'name', 'image', 'cooking_time')
        read_only_fields = ('id',)


class RecipeSerializer(serializers.ModelSerializer):
    author = UserSerializer(read_only=True)
    ingredients = IngredientInRecipeSerializer(many=True, read_only=True)
    is_favorited = serializers.SerializerMethodField()
    is_in_shopping_cart = serializers.SerializerMethodField()
    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id', 'author', 'ingredients', 'is_favorited',
            'is_in_shopping_cart', 'name', 'image', 'text', 'cooking_time'
        )
        read_only_fields = (
            'id', 'author', 'is_favorited', 'is_in_shopping_cart'
        )

    def get_is_favorited(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return Favorite.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False

    def get_is_in_shopping_cart(self, obj):
        request = self.context.get('request')
        if request and request.user.is_authenticated:
            return ShoppingCart.objects.filter(
                user=request.user, recipe=obj
            ).exists()
        return False


class RecipeWithShortLinkSerializer(RecipeSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta(RecipeSerializer.Meta):
        fields = RecipeSerializer.Meta.fields + ('short_link',)
        read_only_fields = RecipeSerializer.Meta.read_only_fields + (
            'short_link',
        )

    def get_short_link(self, obj):
        request = self.context.get('request')
        short_link, created = ShortLink.objects.get_or_create(
            recipe=obj, defaults={'short_code': str(uuid.uuid4())[:8]}
        )
        base_url = request.build_absolute_uri('/')[:-1]
        return f"{base_url}/s/{short_link.short_code}"


class RecipeCreateUpdateSerializer(serializers.ModelSerializer):
    ingredients = serializers.ListField(
        child=serializers.DictField(
            child=serializers.IntegerField(),
            required=True,
            allow_null=False
        ),
        write_only=True,
        required=True
    )
    image = Base64ImageField(required=True)
    name = serializers.CharField(
        required=True, allow_blank=False, max_length=256
    )
    text = serializers.CharField(required=True, allow_blank=False)
    cooking_time = serializers.IntegerField(required=True, min_value=1)

    class Meta:
        model = Recipe
        fields = (
            'id', 'ingredients', 'image', 'name', 'text', 'cooking_time'
        )
        read_only_fields = ('id',)

    def validate_name(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Поле 'name' не может быть пустым."
            )
        if len(value) > 256:
            raise serializers.ValidationError(
                "Поле 'name' не может превышать 256 символов."
            )
        return value

    def validate_text(self, value):
        if not value.strip():
            raise serializers.ValidationError(
                "Поле 'text' не может быть пустым."
            )
        return value

    def validate_cooking_time(self, value):
        if value < 1:
            raise serializers.ValidationError(
                "Время приготовления должно быть больше или равно 1."
            )
        return value

    def validate_ingredients(self, value):
        if not value:
            raise serializers.ValidationError(
                "Добавьте хотя бы один ингредиент."
            )

        ingredient_ids = set()
        for item in value:
            if not isinstance(item, dict) or 'id' not in item or 'amount' not in item:
                raise serializers.ValidationError(
                    "Каждый ингредиент должен быть объектом с полями id и "
                    "amount."
                )

            amount = item['amount']
            if not isinstance(amount, int) or amount < 1:
                raise serializers.ValidationError(
                    "Количество должно быть целым числом >= 1."
                )

            if not Ingredient.objects.filter(id=item['id']).exists():
                raise serializers.ValidationError(
                    f"Ингредиент с id {item['id']} не существует."
                )

            ingredient_ids.add(item['id'])

        if len(ingredient_ids) != len(value):
            raise serializers.ValidationError(
                "Ингредиенты не должны повторяться."
            )

        return value

    def create_ingredients(self, ingredients_data, recipe):
        ingredients = [
            IngredientInRecipe(
                recipe=recipe,
                ingredient=Ingredient.objects.get(id=item['id']),
                amount=item['amount']
            )
            for item in ingredients_data
        ]
        IngredientInRecipe.objects.bulk_create(ingredients)

    def create(self, validated_data):
        ingredients_data = validated_data.pop('ingredients')
        validated_data['author'] = self.context['request'].user
        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients_data, recipe)
        return recipe

    def update(self, instance, validated_data):
        if 'ingredients' not in validated_data:
            raise serializers.ValidationError(
                {"ingredients": "Это поле обязательно."}
            )

        ingredients_data = validated_data.pop('ingredients')
        validated_data.pop('author', None)
        if 'name' in validated_data and not validated_data['name'].strip():
            raise serializers.ValidationError(
                "Поле 'name' не может быть пустым."
            )
        if 'text' in validated_data and not validated_data['text'].strip():
            raise serializers.ValidationError(
                "Поле 'text' не может быть пустым."
            )
        if ('cooking_time' in validated_data
                and validated_data['cooking_time'] < 1):
            raise serializers.ValidationError(
                "Время приготовления должно быть больше или равно 1."
            )
        instance = super().update(instance, validated_data)
        instance.ingredients.all().delete()
        self.create_ingredients(ingredients_data, instance)
        return instance


class ShortLinkSerializer(serializers.ModelSerializer):
    short_link = serializers.SerializerMethodField()

    class Meta:
        model = ShortLink
        fields = ('short_link',)

    def get_short_link(self, obj):
        request = self.context.get('request')
        base_url = request.build_absolute_uri('/')[:-1]
        return f"{base_url}/s/{obj.short_code}"


class CustomTokenCreateSerializer(BaseTokenCreateSerializer):
    def validate(self, attrs):
        possible_email_fields = [
            'username', 'login', 'user', 'userName', 'emailAddress'
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
