from .models import ArticleView, Article, Follow
import math
from django.utils import timezone


def get_viewed_articles(user, anon_id):
    if user.is_authenticated:
        viewed_articles = user.viewed_articles.all().select_related('article')
    else:
        viewed_articles = ArticleView.objects.filter(anonymous_id=anon_id).select_related('article')
    return [item.article for item in viewed_articles]


def get_tags_count(user, anon_id):
    viewed_articles = get_viewed_articles(user, anon_id)
    tags_count = {}

    for article in viewed_articles:
        for tag in article.tags.all():
            count = tags_count.get(tag.id, 0)
            count+=1
            tags_count[tag.id] = count

    return tags_count


def engament_score(article):
    return math.log(article.likes_count + 1) * 3 + math.log(article.comments.count() + 1) * 2 + math.log(article.views_count+1)


def get_feed(user, anon_id):
    tags_count = get_tags_count(user, anon_id)

    if user.is_authenticated:
        viewed_articles_id = user.viewed_articles.values_list("article_id", flat=True)
    else:
        viewed_articles_id = ArticleView.objects.filter(anonymous_id=anon_id).values_list('article_id', flat=True)

    following_ids = []
    if user.is_authenticated:
        following_ids = Follow.objects.filter(follower = user).values_list('following.id', flat=True)

    candidate_articles = Article.objects.exclude(id__in = viewed_articles_id).order_by("-created_at")[:100]

    scored_articles = []
    for article in candidate_articles:
        score = 0

        # follower scoring
        if article.author.id in following_ids:
            score += 50

        # tag scoring
        for tag in article.tags.all():
            score += tags_count.get(tag.id, 0) * 5

        # engagemnet
        score += engament_score(article)

        # freshness
        now = timezone.now()
        days_after = (now - article.created_at).days

        score += max(0, (30 - days_after))

        scored_articles.append((score, article))

    scored_articles.sort(key=lambda item: (-item[0], -item[1].id))
    return [article for _, article in scored_articles[:10]]