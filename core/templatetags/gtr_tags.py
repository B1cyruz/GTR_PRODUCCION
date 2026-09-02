from django import template

register = template.Library()

@register.filter(name='replace')
def replace(value, arg):
    """Reemplaza caracteres en strings: value|replace:'_, '"""
    if not value or not isinstance(value, str):
        return value
    if ',' in arg:
        old, new = arg.split(',', 1)
        return value.replace(old, new)
    return value.replace(arg, ' ')

@register.filter(name='replace_underscore')
def replace_underscore(value):
    if not value or not isinstance(value, str):
        return value
    return value.replace('_', ' ')

@register.filter(name='get_initials')
def get_initials(name):
    if not name:
        return "GT"
    parts = str(name).strip().split()
    if len(parts) >= 2:
        return (parts[0][0] + parts[1][0]).upper()
    return str(name)[:2].upper()

@register.filter(name='count_by_role')
def count_by_role(user_list, role_name):
    if not user_list:
        return 0
    count = 0
    for u in user_list:
        u_role = getattr(u, 'role', None) if not isinstance(u, dict) else u.get('role')
        if str(u_role).upper() == str(role_name).upper():
            count += 1
    return count
