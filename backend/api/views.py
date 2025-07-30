from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.exceptions import ValidationError, PermissionDenied
from django.shortcuts import get_object_or_404
from django.db.models import Sum
from django.http import FileResponse
from django.urls import reverse
from recipes.models import (
    User,
    Subscription,
    Product,
    Recipe,
    ProductInRecipe,
    Favorite,
    ShoppingCart
)
from .serializers import (
    UserSerializer,
    UserCreateSerializer,
    UserWithRecipesSerializer,
    SetAvatarSerializer,
    SetAvatarResponseSerializer,
    ProductSerializer,
    RecipeSerializer,
    RecipeCreateUpdateSerializer,
    RecipeMinifiedSerializer
)
from .permissions import IsAuthorOrReadOnly
from .pagination import StandardResultsSetPagination
from django_filters.rest_framework import DjangoFilterBackend
from .filters import ProductFilter, RecipeFilter
from djoser.views import UserViewSet as DjoserUserViewSet
from datetime import datetime
from io import StringIO
import uuid
import re


class UserViewSet(DjoserUserViewSet):
    queryset = User.objects.all().order_by('id')
    serializer_class = UserSerializer
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'email']

    def get_permissions(self):
        if self.action in ['list', 'retrieve']:
            return [AllowAny()]
        return (
            [IsAuthenticated()]
            if self.action == 'me'
            else super().get_permissions()
        )

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = UserSerializer(
            page or queryset,
            many=True,
            context={'request': request}
        )
        data = serializer.data
        return self.get_paginated_response(data) if page else Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': data
        })

    def retrieve(self, request, *args, **kwargs):
        return Response(
            self.get_serializer(
                self.get_object(),
                context={'request': request}
            ).data
        )

    def create(self, request, *args, **kwargs):
        serializer = UserCreateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            serializer.data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserWithRecipesSerializer
    )
    def subscriptions(self, request):
        queryset = User.objects.filter(authors__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = UserWithRecipesSerializer(
            page or queryset,
            many=True,
            context={'request': request}
        )
        data = serializer.data
        return self.get_paginated_response(data) if page else Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': data
        })

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated],
        serializer_class=UserWithRecipesSerializer
    )
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, pk=id)
        if request.method == 'POST':
            if user == author:
                raise ValidationError("Нельзя подписаться на самого себя.")
            if Subscription.objects.filter(user=user, author=author).exists():
                raise ValidationError(
                    f"Вы уже подписаны на пользователя {author.username}."
                )
            Subscription.objects.create(user=user, author=author)
            return Response(
                UserWithRecipesSerializer(
                    author,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        if not Subscription.objects.filter(user=user, author=author).exists():
            raise ValidationError(
                "Вы не подписаны на этого пользователя.",
                code=400
            )
        Subscription.objects.filter(user=user, author=author).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=False,
        methods=['put', 'delete'],
        permission_classes=[IsAuthenticated],
        url_path='me/avatar'
    )
    def me_avatar(self, request):
        user = request.user
        if request.method == 'PUT':
            serializer = SetAvatarSerializer(
                data=request.data,
                instance=user
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(
                SetAvatarResponseSerializer(user).data,
                status=status.HTTP_200_OK
            )
        if not user.avatar:
            raise ValidationError("Аватар отсутствует.")
        user.avatar.delete(save=True)
        return Response(status=status.HTTP_204_NO_CONTENT)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = Product.objects.all()
    serializer_class = ProductSerializer
    permission_classes = [AllowAny]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ProductFilter
    pagination_class = None


class RecipeViewSet(viewsets.ModelViewSet):
    queryset = Recipe.objects.all().select_related(
        'author').prefetch_related('products')
    permission_classes = [IsAuthorOrReadOnly]
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_class = RecipeFilter

    def get_filter_backends(self):
        if self.action == 'list':
            return [DjangoFilterBackend]
        return []

    def get_serializer_class(self):
        return RecipeCreateUpdateSerializer if self.action in [
            'create', 'update', 'partial_update'
        ] else RecipeSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = RecipeSerializer(
            page or queryset,
            many=True,
            context={'request': request}
        )
        data = serializer.data
        return self.get_paginated_response(data) if page else Response({
            'count': queryset.count(),
            'next': None,
            'previous': None,
            'results': data
        })

    def retrieve(self, request, *args, **kwargs):
        return Response(
            RecipeSerializer(
                self.get_object(),
                context={'request': request}
            ).data
        )

    def create(self, request, *args, **kwargs):
        serializer = RecipeCreateUpdateSerializer(
            data=request.data,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(
            RecipeSerializer(
                serializer.instance,
                context={'request': request}
            ).data,
            status=status.HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    def partial_update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.author != self.request.user:
            raise PermissionDenied("Только автор может обновлять рецепт.")
        serializer = RecipeCreateUpdateSerializer(
            instance,
            data=request.data,
            partial=True,
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(
            RecipeSerializer(
                instance,
                context={'request': request}
            ).data
        )

    def perform_update(self, serializer):
        serializer.save()

    def perform_destroy(self, instance):
        if instance.author != self.request.user:
            raise PermissionDenied("Только автор может удалять рецепт.")
        instance.delete()

    @staticmethod
    def toggle_relation(model, user, recipe, request, relation_name):
        if request.method == 'POST':
            if model.objects.filter(user=user, recipe=recipe).exists():
                raise ValidationError(
                    f"Рецепт '{recipe.name}' уже в {relation_name}.",
                    code=400
                )
            model.objects.create(user=user, recipe=recipe)
            return Response(
                RecipeMinifiedSerializer(
                    recipe,
                    context={'request': request}
                ).data,
                status=status.HTTP_201_CREATED
            )
        if not model.objects.filter(user=user, recipe=recipe).exists():
            raise ValidationError(
                f"Рецепт '{recipe.name}' не находится в {relation_name}.",
                code=400
            )
        model.objects.filter(user=user, recipe=recipe).delete()
        return Response(status=status.HTTP_204_NO_CONTENT)

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def favorite(self, request, pk=None):
        return self.toggle_relation(
            Favorite,
            request.user,
            get_object_or_404(Recipe, pk=pk),
            request,
            "избранном"
        )

    @action(
        detail=True,
        methods=['post', 'delete'],
        permission_classes=[IsAuthenticated]
    )
    def shopping_cart(self, request, pk=None):
        return self.toggle_relation(
            ShoppingCart,
            request.user,
            get_object_or_404(Recipe, pk=pk),
            request,
            "списке покупок"
        )

    @action(
        detail=True,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path='get-link'
    )
    def get_link(self, request, pk=None):
        recipe = get_object_or_404(Recipe, pk=pk)
        short_code = f"{recipe.id}-{str(uuid.uuid4())[:8]}"
        base_url = request.build_absolute_uri('/')[:-1]
        return Response(
            {'short-link': f"{base_url}/s/{short_code}"},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[AllowAny],
        url_path=r's/(?P<short_code>[^/.]+)'
    )
    def short_link_redirect(self, request, short_code=None):
        match = re.match(r'^(\d+)-', short_code)
        if not match:
            raise ValidationError(
                "Неверный формат короткой ссылки.",
                code=400
            )
        recipe_id = match.group(1)
        recipe = get_object_or_404(Recipe, id=recipe_id)
        recipe_url = reverse(
            'recipe-detail',
            args=[recipe.id],
            request=request
        )
        return Response(
            {'url': recipe_url},
            status=status.HTTP_200_OK
        )

    @action(
        detail=False,
        methods=['get'],
        permission_classes=[IsAuthenticated],
        url_path='download_shopping_cart'
    )
    def download_shopping_cart(self, request):
        user = request.user
        products = ProductInRecipe.objects.filter(
            recipe__shopping_carts__user=user,
            amount__gte=1
        ).exclude(
            amount=0
        ).select_related('ingredient').values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(
            total_amount=Sum('amount')
        ).order_by('ingredient__name')
        recipes = Recipe.objects.filter(
            shopping_carts__user=user
        ).select_related('author')
        current_date = datetime.now().strftime('%Y-%m-%d %H:%M')
        content = (
            f"Список покупок от {current_date} \n\n" + (
                "Ваш список покупок пуст.\n" if not products else
                "Продукты:\n" + "\n".join(
                    f"{idx}. {item['ingredient__name'].capitalize()} - "
                    f"{item['total_amount']} "
                    f"{item['ingredient__measurement_unit']}"
                    for idx, item in enumerate(products, 1)
                ) + "\n\nРецепты в списке:\n" + "\n".join(
                    f"{idx}. {recipe.name} (автор: {recipe.author.username})"
                    for idx, recipe in enumerate(recipes, 1)
                )
            )
        )
        buffer = StringIO(content)
        return FileResponse(
            buffer,
            as_attachment=True,
            filename="shopping_list.txt",
            content_type='text/plain; charset=utf-8'
        )
