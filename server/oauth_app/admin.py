from django.contrib import admin

from oauth_app.models import OAuthConsumer, OAuthRequestToken, OAuthAccessToken

class OAuthConsumerAdmin(admin.ModelAdmin):
    list_display = ('key', 'user')

class TokenAdmin(admin.ModelAdmin):
    list_display = ('key', 'user', 'status', 'consumer', 'created')
    ordering = '-created', 
    
class ErrorAdmin(admin.ModelAdmin):
    list_display = ('user', 'created')
    ordering = '-created', 
    
    
admin.site.register(OAuthConsumer, OAuthConsumerAdmin)
admin.site.register(OAuthRequestToken, TokenAdmin)
admin.site.register(OAuthAccessToken, TokenAdmin)
