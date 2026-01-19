from django.contrib.auth.models import UserManager as DjangoUserManager


class UserManager(DjangoUserManager):
    def create_user(self, email, password=None, username=None, **extra_fields):
        if not username:
            base_username = (email or "").split("@")[0] if email else "user"
            username = base_username
            num = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{num}"
                num += 1
        return super().create_user(username=username, email=email, password=password, **extra_fields)

    def create_superuser(self, email, password=None, username=None, **extra_fields):
        if not username:
            base_username = (email or "").split("@")[0] if email else "admin"
            username = base_username
            num = 1
            while self.model.objects.filter(username=username).exists():
                username = f"{base_username}{num}"
                num += 1
        return super().create_superuser(username=username, email=email, password=password, **extra_fields)
