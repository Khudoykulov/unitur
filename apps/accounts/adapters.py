from allauth.account.adapter import DefaultAccountAdapter


class AccountAdapter(DefaultAccountAdapter):
    def get_login_redirect_url(self, request):
        if request.user.is_staff:
            return "/dashboard/"
        return super().get_login_redirect_url(request)
