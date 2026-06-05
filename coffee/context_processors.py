def role_flags(request):
    user = getattr(request, 'user', None)
    is_receptionist = False
    is_admin_superior = False
    try:
        if user and user.is_authenticated:
            # Superusers and staff are considered admin_superior
            if user.is_superuser or user.is_staff:
                is_receptionist = user.is_superuser or ('receptionist' in [g.lower() for g in user.groups.values_list('name', flat=True)])
                is_admin_superior = True
            else:
                groups = [g.lower() for g in user.groups.values_list('name', flat=True)]
                is_receptionist = 'receptionist' in groups or 'recepcionista' in groups
                is_admin_superior = 'adminsuperior' in groups or 'admin_superior' in groups
    except Exception:
        pass
    return {'is_receptionist': is_receptionist, 'is_admin_superior': is_admin_superior}
