from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django.db import transaction
from .models import Post, PostMedia, PostReaction, Comment, CommentReaction, Share
from .serializers import PostSerializer, CommentSerializer

class PostViewSet(viewsets.ModelViewSet):
    queryset = (
        Post.objects
        .select_related("author")
        .prefetch_related("media", "reactions", "comments")
        .order_by("-created_at")  # 🟢 thêm dòng này
    )
    serializer_class = PostSerializer

    def get_permissions(self):
        return [permissions.AllowAny()] if self.action in ["list","retrieve"] else [permissions.IsAuthenticated()]

    def perform_create(self, serializer):
        serializer.save(author=self.request.user)

    @transaction.atomic
    def create(self, request, *args, **kwargs):
        kind = request.data.get("kind", "normal")
        content_text = request.data.get("content") or ""
        content_medical = request.data.get("content_medical")
        p = Post.objects.create(
            author=request.user,
            kind=kind,
            content_text=content_text if kind=="normal" else None,
            content_medical=content_medical if kind=="medical" else None,
            visibility=request.data.get("visibility","public"),
        )
        for f in request.FILES.getlist("media"):
            mt = "video" if (getattr(f,"content_type","").startswith("video")) else "image"
            PostMedia.objects.create(post=p, file=f, media_type=mt)
        return Response(PostSerializer(p, context={"request": request}).data, status=201)

    @action(detail=True, methods=["post", "delete"], url_path="reactions")
    def reactions(self, request, pk=None):
        post = self.get_object()
        if request.method == "DELETE":
            PostReaction.objects.filter(post=post, user=request.user).delete()
            return Response({"ok": True})
        rtype = request.data.get("type")
        if not rtype: return Response({"error": "Missing type"}, status=400)
        PostReaction.objects.update_or_create(post=post, user=request.user, defaults={"type": rtype})
        return Response({"ok": True, "type": rtype})

    @action(detail=True, methods=["post"], url_path="share")
    def share(self, request, pk=None):
        post = self.get_object()
        Share.objects.create(post=post, user=request.user, message=request.data.get("message",""))
        return Response({"ok": True, "shares": post.shares.count()})

class CommentViewSet(viewsets.GenericViewSet):
    queryset = Comment.objects.select_related("author","post").prefetch_related("replies","reactions")
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = CommentSerializer

    def list(self, request):
        post_id = request.query_params.get("post")
        if not post_id: return Response({"error":"Missing post"}, status=400)
        roots = Comment.objects.filter(post_id=post_id, parent__isnull=True).order_by("created_at")
        return Response(CommentSerializer(roots, many=True, context={"request": request}).data)

    def create(self, request):
        post_id = request.data.get("post")
        text = (request.data.get("text") or "").strip()
        parent_id = request.data.get("parent")
        if not post_id or not text: return Response({"error":"Missing post/text"}, status=400)
        c = Comment.objects.create(post_id=post_id, author=request.user, text=text, parent_id=parent_id or None)
        return Response(CommentSerializer(c, context={"request": request}).data, status=201)

    def partial_update(self, request, pk=None):
        c = self.get_queryset().get(pk=pk, author=request.user)
        c.text = (request.data.get("text") or c.text).strip()
        c.save()
        return Response(CommentSerializer(c, context={"request": request}).data)

    def destroy(self, request, pk=None):
        c = self.get_queryset().get(pk=pk, author=request.user)
        c.delete()
        return Response(status=204)

    @action(detail=True, methods=["post","delete"], url_path="reactions")
    def reactions(self, request, pk=None):
        c = self.get_queryset().get(pk=pk)
        if request.method == "DELETE":
            CommentReaction.objects.filter(comment=c, user=request.user).delete()
            return Response({"ok": True})
        rtype = request.data.get("type")
        if not rtype: return Response({"error":"Missing type"}, status=400)
        CommentReaction.objects.update_or_create(comment=c, user=request.user, defaults={"type": rtype})
        return Response({"ok": True, "type": rtype})
