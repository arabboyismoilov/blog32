from rest_framework.response import Response
from rest_framework.generics import CreateAPIView
from .serializers import (SignUpSerializer, TagSerializer, ArticleSerializer, 
                          CommentSerializer, ArticleReactionSerializer,
                          FollowSerializer, ProfileSerializer, ArticleViewSerializer, ArticleDetailSerializer)
from drf_spectacular.utils import extend_schema
from rest_framework.viewsets import ModelViewSet
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, RetrieveAPIView, UpdateAPIView, ListAPIView
from .models import Tag, Article, Comment, ArticleReaction, Follow, ArticleView
from rest_framework.permissions import IsAuthenticated, BasePermission
from rest_framework.exceptions import NotFound
from rest_framework.views import APIView
from django.contrib.auth import get_user_model
from drf_spectacular.utils import OpenApiParameter
from drf_spectacular.types import OpenApiTypes
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView


User = get_user_model()


class IsOwner(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj.author == request.user
    

class IsUserItself(BasePermission):
    def has_object_permission(self, request, view, obj):
        return obj == request.user


@extend_schema(
        request=SignUpSerializer,
        responses={201: SignUpSerializer},
        tags=['auth']
    )
class SignUpView(CreateAPIView):
    serializer_class = SignUpSerializer


@extend_schema(
    tags=['tags']
)
class TagsModelViewSet(ModelViewSet):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()


@extend_schema(
    tags=['user_articles']
)
class UserArticleListCreateApiView(ListCreateAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        serializer.save(author = self.request.user)

    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)


@extend_schema(
    tags=['user_articles']
)
class UserArticleDetailView(RetrieveUpdateDestroyAPIView):
    serializer_class = ArticleSerializer
    permission_classes = [IsAuthenticated, IsOwner]
    
    def get_queryset(self):
        return Article.objects.filter(author=self.request.user)
    

@extend_schema(
    tags=['comments']
)
class CommentListCreateApiView(ListCreateAPIView):
    serializer_class = CommentSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        article_id = self.kwargs['article_id']
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            raise NotFound(detail=f"Article with {article_id} not found")
        serializer.save(user=self.request.user, article=article)

    def get_queryset(self):
        article_id = self.kwargs['article_id']
        return Comment.objects.filter(article__id = article_id)
    

@extend_schema(
    tags=['reactions']
)
class ArticleReactionCreateDeleteApiView(ListCreateAPIView):
    serializer_class = ArticleReactionSerializer
    permission_classes = [IsAuthenticated]

    def perform_create(self, serializer):
        reaction_type = serializer.validated_data["reaction"]
        article_id = self.kwargs['article_id']
        try:
            article = Article.objects.get(pk=article_id)
        except Article.DoesNotExist:
            raise NotFound(detail=f"Article with {article_id} not found")
        
        reaction, created = ArticleReaction.objects.get_or_create(user=self.request.user, article=article, reaction=reaction_type)
        if not created:
            reaction.delete()
            if reaction_type == 'dislike':
                article.dislikes_count -= 1
                article.save()
            else:
                article.likes_count -= 1
                article.save()
            return Response(data={
                "detail": "deleted"
            })
        if reaction_type == 'dislike':
            article.dislikes_count += 1
            article.save()
        else:
            article.likes_count += 1
            article.save()
        return Response(data={
            "detail": "created"
        })

    def get_queryset(self):
        article_id = self.kwargs['article_id']
        return ArticleReaction.objects.filter(article__id = article_id)
    

@extend_schema(
    tags=['follows']
)
class FollowCreateApiView(CreateAPIView):
    serializer_class = FollowSerializer
    permission_classes = [IsAuthenticated]

    def create(self, request, *args, **kwargs):
        serializer = FollowSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        user = self.request.user

        following = serializer.validated_data.get("following")
        follow, created = Follow.objects.get_or_create(follower=user, following=following)

        if not created:
            follow.delete()

            user.following_count -= 1
            user.save()

            following.follower_count -= 1
            following.save()

            return Response(data={
                "detail": "unfollowed"
            })
        else:
            user.following_count += 1
            user.save()

            following.follower_count += 1
            following.save()
            return Response(data={
                "detail": "followed"
            })
        

@extend_schema(
    tags=['public']
)
class ProfileDetailView(RetrieveAPIView):
    serializer_class = ProfileSerializer
    queryset = User
    lookup_field = 'username'

@extend_schema(
    tags=['user']
)
class ProfileUpdateView(UpdateAPIView):
    permission_classes = [IsAuthenticated]
    serializer_class = ProfileSerializer

    def get_object(self):
        return self.request.user
    
@extend_schema(
    tags=['public']
)
class ArticleViewCreateApiView(CreateAPIView):
    serializer_class = ArticleViewSerializer

    def create(self, request, *args, **kwargs):
        serializer = ArticleViewSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        article = serializer.validated_data.get("article")
        anon_id = serializer.validated_data.get("anonymous_id")
        user = request.user

        if user.is_authenticated:
            _, created = ArticleView.objects.get_or_create(article=article, user=user)
            if created:
                article.views_count += 1
                article.save()
                return Response(data={
                    "detail": "newly viewed"
                })
            else:
                return Response(data={
                    "detail": "previously viewed"
                })
        else:
            _, created = ArticleView.objects.get_or_create(article=article, anonymous_id=anon_id)
            if created:
                article.views_count += 1
                article.save()
                return Response(data={
                    "detail": "newly viewed"
                })
            else:
                return Response(data={
                    "detail": "previously viewed"
                })

@extend_schema(
    tags=['public']
)           
class ArticleDetailPublicView(RetrieveAPIView):
    serializer_class = ArticleDetailSerializer
    queryset = Article.objects.all()

from .recommendation_engine import get_feed
@extend_schema(
    tags=['public']
)
class FeedApiView(APIView):
    @extend_schema(
        summary="Retrieve article feed",
        description="Fetch a list of articles based on the user or an anonymous ID.",
        parameters=[
            OpenApiParameter(
                name="Anonymous-ID",
                type=OpenApiTypes.STR,
                location=OpenApiParameter.HEADER,
                description="Unique identifier for guest users",
                required=False,
            )
        ],
        responses={200: ArticleSerializer(many=True)},
    )
    def get(self, request):
        anon_id = self.request.headers.get("Anonymous-ID")
        results = get_feed(self.request.user, anon_id)
        serialzier = ArticleSerializer(results, many=True)
        return Response(data=serialzier.data)  
    
@extend_schema(
    tags=['comments']
)
class CommentDetailView(RetrieveUpdateDestroyAPIView):
    permission_classes = [IsAuthenticated, IsOwner]
    serializer_class = CommentSerializer
    queryset = Comment.objects.all()


@extend_schema(
    tags=['auth']
)
class LoginView(TokenObtainPairView):
    pass


@extend_schema(
    tags=['auth']
)
class RefreshTokenView(TokenRefreshView):
    pass