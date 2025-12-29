from django.apps import AppConfig

class AccountsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'accounts'
    def ready(self):
        # Ensure default groups and permissions exist. Wrapped in try/except
        # because during initial migrations the auth tables may not be available.
        try:
            from django.contrib.auth.models import Group, Permission
            from django.contrib.contenttypes.models import ContentType
            from django.apps import apps
            from django.db import OperationalError, ProgrammingError

            finance_models = ['Expense', 'Category', 'Budget', 'ExpenseAttachment', 'RefundRequest']

            # Group definitions: permissions granted per group
            groups_spec = {
                'System Admin': {'all_permissions': True},
                'Homeowner': {'models': ['Expense', 'Category', 'Budget', 'ExpenseAttachment'], 'perms': ['add', 'change', 'delete', 'view']},
                'Helper': {'models': ['Expense', 'ExpenseAttachment'], 'perms': ['add', 'change', 'view']},
                'Viewer': {'models': ['Expense', 'Category'], 'perms': ['view']},
            }

            for group_name, spec in groups_spec.items():
                group, created = Group.objects.get_or_create(name=group_name)
                if spec.get('all_permissions'):
                    # assign all permissions across installed apps
                    perms = Permission.objects.all()
                    group.permissions.set(perms)
                    continue

                perms_to_assign = []
                for model_name in spec.get('models', []):
                    try:
                        model = apps.get_model('finances', model_name)
                    except LookupError:
                        continue
                    ct = ContentType.objects.get_for_model(model)
                    for p in spec.get('perms', []):
                        codename = f"{p}_{model_name.lower()}"
                        perm = Permission.objects.filter(codename=codename, content_type=ct).first()
                        if perm:
                            perms_to_assign.append(perm)

                if perms_to_assign:
                    group.permissions.add(*perms_to_assign)

        except (OperationalError, ProgrammingError, Exception):
            # DB not ready or migrations not applied; skip group creation for now.
            pass