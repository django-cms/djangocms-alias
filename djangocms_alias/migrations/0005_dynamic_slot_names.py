from django.db import migrations


def migrate_slots(apps, schema_editor, forward=True):
    AliasContent = apps.get_model("djangocms_alias", "AliasContent")

    db_alias = schema_editor.connection.alias
    qs = AliasContent.objects.using(db_alias).prefetch_related("alias").exclude(alias__static_code="")

    for alias_content in qs:
        slots = list(alias_content.placeholders.all())
        if len(slots) == 1:
            placeholder = slots[0]
            # Ensure the placeholder exists with the correct slot name
            if forward and placeholder.slot == alias_content.placeholder_slotname:
                # If migrating forward, we use the static code or the placeholder slot name
                placeholder.slot = alias_content.alias.static_code or alias_content.placeholder_slotname
                placeholder.save()
            elif placeholder.slot != alias_content.placeholder_slotname:
                # If migrating backward, we revert to the original placeholder slot name
                placeholder.slot = alias_content.placeholder_slotname
                placeholder.save()
        elif len(slots) > 1:
            print(
                f"AliasContent {alias_content.pk} has multiple placeholders, expected only one. "
                "Skipping migration for this instance."
            )


class Migration(migrations.Migration):
    dependencies = [
        ("djangocms_alias", "0004_alter_aliascontent_language"),
    ]

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: migrate_slots(apps, schema_editor, forward=True),
            reverse_code=lambda apps, schema_editor: migrate_slots(apps, schema_editor, forward=False),
            elidable=True,
        ),
    ]
