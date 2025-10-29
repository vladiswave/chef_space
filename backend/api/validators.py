from django.core.validators import RegexValidator

validate_username_regex = RegexValidator(
    r'^[\w.@+-]+\Z',
    'Username должен состоять из букв, цифр и символов @.+-_'
)
