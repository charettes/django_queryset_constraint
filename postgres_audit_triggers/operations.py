from django.db.migrations.operations.base import Operation
from django.utils.functional import cached_property


__all__ = (
    'AddAuditTrigger',
    'RemoveAuditTrigger',
)


class AddAuditTrigger(Operation):
    reduces_to_sql = True
    reversible = True
    option_name = 'audit_trigger'

    def __init__(self, model_name):
        self.name = model_name

    @cached_property
    def model_name_lower(self):
        return self.name.lower()

    def state_forwards(self, app_label, state):
        model_state = state.models[app_label, self.model_name_lower]
        audit_trigger = model_state.options.get(self.option_name, False)
        model_state.options[self.option_name] = audit_trigger
        state.reload_model(app_label, self.model_name_lower, delay=True)

    def database_forwards(
        self, app_label, schema_editor, from_state, to_state,
    ):
        model = to_state.apps.get_model(app_label, self.name)
        table = model._meta.db_table
        schema_editor.execute(
            'SELECT audit.audit_table(\'{}\')'.format(table),
        )

    def database_backwards(
        self, app_label, schema_editor, from_state, to_state,
    ):
        model = to_state.apps.get_model(app_label, self.name)
        table = model._meta.db_table
        schema_editor.execute(
            'DROP TRIGGER audit_trigger_row ON {}'.format(table),
        )
        schema_editor.execute(
            'DROP TRIGGER audit_trigger_stm ON {}'.format(table),
        )

    def describe(self):
        return 'Add audit triggers on model {}'.format(self.name)


class RemoveAuditTrigger(AddAuditTrigger):
    def database_forwards(
        self, app_label, schema_editor, from_state, to_state,
    ):
        super().database_backwards(
            app_label, schema_editor, from_state, to_state,
        )

    def database_backwards(
        self, app_label, schema_editor, from_state, to_state,
    ):
        super().database_forwards(
            app_label, schema_editor, from_state, to_state,
        )

    def describe(self):
        return 'Remove audit triggers on model {}'.format(self.name)