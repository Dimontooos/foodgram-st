from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.permissions import (
    IsAuthenticated, AllowAny, IsAuthenticatedOrReadOnly
)
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import HttpResponse
import uuid
from users.models import User, Subscription
from recipes.models import (
    Ingredient, Recipe, IngredientInRecipe, Favorite, ShoppingCart, ShortLink
)
from .serializers import (
    MinimalUserSerializer, UserSerializer, UserWithRecipesSerializer,
    SetAvatarSerializer, SetAvatarResponseSerializer, IngredientSerializer,
    RecipeSerializer, RecipeCreateUpdateSerializer, RecipeMinifiedSerializer,
    ShortLinkSerializer, CustomUserCreateSerializer, SetPasswordSerializer,
    RecipeWithShortLinkSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import IngredientFilter, RecipeFilter


class UserViewSet(viewsets.ModelViewSet):
    queryset = User.objects.all().order_by('id')
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'email']

    def get_permissions(self):
        if self.action == 'create':
            return [AllowAny()]
        return super().get_permissions()

    def get_serializer_class(self):
        if self.action == 'subscriptions':
            return UserWithRecipesSerializer
        elif self.action == 'create':
            return CustomUserCreateSerializer
        elif self.action == 'set_password':
            return SetPasswordSerializer
        elif self.action in ['retrieve', 'me', 'list']:
            return UserSerializer
        return MinimalUserSerializer

    def get_paginator(self):
        if self.action in ['retrieve', 'me']:
            return None
        return super().get_paginator()

    def create(self, request, *args, **kwargs):
        serializer = CustomUserCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            MinimalUserSerializer(user, context={'request': request}).data,
            status=status.HTTP_201_CREATED
        )

    def retrieve(self, request, *args, **kwargs):
        instance = get_object_or_404(User, pk=self.kwargs.get('pk'))
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    @action(
        detail=False,
        methods=['post'],
        permission_classes=[IsAuthenticated],
        url_path='set_password'
    )
    def set_password(self, request):
        serializer = SetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = request.user
        if not user.check_password(serializer.validated_data['current_password']):
            return Response(
                {"current_password": "Неверный текущий пароль."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated]
    )
    def subscriptions(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Аутентификация не предоставлена."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        queryset = User.objects.filter(subscribers__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page, many=True, context={'request': request}
        )
        return self.get_paginated_response(serializer.data)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def subscribe(self, request, pk=None):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Аутентификация не предоставлена."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        author = get_object_or_404(User, pk=pk)
        if user == author:
            return Response(
                {"detail": "Нельзя подписаться на самого себя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        if request.method == 'POST':
            if Subscription.objects.filter(user=user, author=author).exists():
                return Response(
                    {"detail": "Вы уже подписаны на этого пользователя."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Subscription.objects.create(user=user, author=author)
            serializer = UserWithRecipesSerializer(
                author, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        subscription = Subscription.objects.filter(
            user=user, author=author
        ).first()
        if not subscription:
            return Response(
                {"detail": "Вы не подписаны на этого пользователя."},
                status=status.HTTP_400_BAD_REQUEST
            )
        subscription.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Аутентификация не предоставлена."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(data=request.data, instance=user)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            response_serializer = SetAvatarResponseSerializer(user)
            return Response(
                response_serializer.data,
                status=status.HTTP_200_OK
            )
        if not user.avatar:
            return Response(
                {"detail": "Аватар отсутствует."},
                status=status.HTTP_400_BAD_REQUEST
            )
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='me'
    )
    def me(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Аутентификация не предоставлена."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        serializer = self.get_serializer(request.user)
        return Response(serializer.data, status=status.HTTP_200_OK)


class IngredientViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Ingredient.objects.all().order_by('name')
    serializer_class = IngredientSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = IngredientFilter
    pagination_class = None

    def get_object(self):
        return get_object_or_404(Ingredient, id=self.kwargs.get('pk'))


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all()
    permission_classes = [IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update']:
            return RecipeCreateUpdateSerializer
        elif self.action == 'get_link':
            return RecipeWithShortLinkSerializer
        return RecipeSerializer

    def get_object(self):
        return get_object_or_404(Recipe, id=self.kwargs.get('pk'))

    def get_queryset(self):
        return Recipe.objects.all().select_related('author').prefetch_related(
            'ingredients'
        )

    def perform_create(self, serializer):
        if not self.request.user.is_authenticated:
            raise ValidationError(
                {"detail": "Требуется аутентификация для создания рецепта."}
            )
        serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        recipe = Recipe.objects.get(id=serializer.data['id'])
        output_serializer = RecipeSerializer(
            recipe, context={'request': request}
        )
        headers = self.get_success_headers(serializer.data)
        return Response(
            output_serializer.data,
            status=status.HTTP_201_CREATED,
            headers=headers
        )

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        if not partial and 'ingredients' not in request.data:
            return Response(
                {"ingredients": "Это поле обязательно."},
                status=status.HTTP_400_BAD_REQUEST
            )
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )
        serializer = self.get_serializer(
            instance, data=request.data, partial=partial
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        output_serializer = RecipeSerializer(
            instance, context={'request': request}
        )
        return Response(output_serializer.data)

    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != request.user:
            return Response(
                {"detail": "Вы не являетесь автором этого рецепта."},
                status=status.HTTP_403_FORBIDDEN
            )
        self.perform_destroy(instance)
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if Favorite.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в избранном."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            Favorite.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        favorite = Favorite.objects.filter(user=user, recipe=recipe).first()
        if not favorite:
            return Response(
                {"detail": "Рецепт не находится в избранном."},
                status=status.HTTP_400_BAD_REQUEST
            )
        favorite.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        user = request.user
        recipe = get_object_or_404(Recipe, pk=pk)
        if request.method == 'POST':
            if ShoppingCart.objects.filter(user=user, recipe=recipe).exists():
                return Response(
                    {"detail": "Рецепт уже в списке покупок."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            ShoppingCart.objects.create(user=user, recipe=recipe)
            serializer = RecipeMinifiedSerializer(
                recipe, context={'request': request}
            )
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        cart_item = ShoppingCart.objects.filter(
            user=user, recipe=recipe
        ).first()
        if not cart_item:
            return Response(
                {"detail": "Рецепт не находится в списке покупок."},
                status=status.HTTP_400_BAD_REQUEST
            )
        cart_item.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = self.get_object()
        short_link, created = ShortLink.objects.get_or_create(
            recipe=recipe,
            defaults={'short_code': str(uuid.uuid4())[:8]}
        )
        serializer = ShortLinkSerializer(
            short_link, context={'request': request}
        )
        return Response(
            {'short-link': serializer.data['short_link']},
            status=status.HTTP_200_OK
        )


class ShoppingCartDownloadView(generics.GenericAPIView):
    permission_classes = [AllowAny]

    def get(self, request):
        if not request.user.is_authenticated:
            return Response(
                {"detail": "Учетные данные не были предоставлены."},
                status=status.HTTP_200_OK
            )

        user = request.user
        try:
            ingredients = IngredientInRecipe.objects.filter(
                recipe__in_shopping_cart__user=user,
                amount__isnull=False,
                amount__gte=1
            ).exclude(
                amount=0
            ).select_related('ingredient').values(
                'ingredient__name', 'ingredient__measurement_unit'
            ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

            content = "=== Список покупок ===\n\n"
            if not ingredients:
                content += "Ваш список покупок пуст.\n"
            else:
                for item in ingredients:
                    name = item.get(
                        'ingredient__name') or 'Неизвестный ингредиент'
                    unit = item.get('ingredient__measurement_unit') or ''
                    amount = item.get('total_amount', 0)
                    content += f"{name} - {amount} {unit}\n"
            response = HttpResponse(
                content_type='text/plain; charset=utf-8',
                headers={
                    'Content-Disposition': 'attachment; '
                    'filename="shopping_list.txt"'
                },
                content=content.encode('utf-8')
            )
            return response
        except Exception as e:
            print(f"Ошибка при формировании списка покупок: {str(e)}")
            return Response(
                {"detail": "Ошибка при формировании списка покупок."},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
