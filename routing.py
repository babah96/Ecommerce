# File: ecommerce/routing.py (project-level channels routing)
# ----------------------------
from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
import shop.routing

application = ProtocolTypeRouter({
    'websocket': AuthMiddlewareStack(
        URLRouter(
            shop.routing.websocket_urlpatterns
        )
    )
})