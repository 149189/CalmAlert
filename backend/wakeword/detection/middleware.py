# detection/middleware.py
from channels.auth import AuthMiddlewareStack
from channels.db import database_sync_to_async
from django.contrib.auth.models import AnonymousUser
from rest_framework.authtoken.models import Token

class TokenAuthMiddleware:
    def __init__(self, inner):
        self.inner = inner

    async def __call__(self, scope, receive, send):
        query_string = scope.get('query_string', b'').decode()
        token_param = [param.split('=')[1] for param in query_string.split('&') if param.startswith('token=')]
        
        if token_param:
            try:
                token = await database_sync_to_async(Token.objects.get)(key=token_param[0])
                scope['user'] = token.user
            except Token.DoesNotExist:
                scope['user'] = AnonymousUser()
        else:
            scope['user'] = AnonymousUser()
            
        return await self.inner(scope, receive, send)

def TokenAuthMiddlewareStack(inner):
    return TokenAuthMiddleware(AuthMiddlewareStack(inner))