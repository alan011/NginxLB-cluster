from geniusalt.models import AuthToken
from datetime import datetime, timedelta
import re

def authenticate(post_data):
    if post_data.get('auth_token'):
        token_str = post_data['auth_token']
        if re.search('^\w+\.\w+$', token_str):
            username = token_str.split('.')[0]
            token    = token_str.split('.')[1]
            queryset = AuthToken.objects.filter(username=username, token=token)
            if queryset.exists():
                obj = queryset.get(username=username, token=token)
                if obj.expired_time == 0:
                    return True
                if obj.sign_date + timedelta(seconds=obj.expired_time) > datetime.now():
                    return True
    return False
