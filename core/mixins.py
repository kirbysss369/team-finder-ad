from core.validators import validate_github_url


class GithubUrlValidationMixin:
    def clean_github_url(self):
        return validate_github_url(self.cleaned_data.get("github_url"))
