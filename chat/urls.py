from rest_framework.routers import DefaultRouter
from .views import ChatRoomViewSet, MessageViewSet

app_name = 'chat'

router = DefaultRouter()
router.register("rooms", ChatRoomViewSet, basename="rooms")
router.register("messages", MessageViewSet, basename="messages")

urlpatterns = router.urls