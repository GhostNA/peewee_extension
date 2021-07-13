import peewee
from peewee import Model, EXCLUDED


class BaseModel(Model):
    def bulk_save(self, rows: list, transaction_count=None):
        conflict_fields = self.get_model_indexes()
        update_fields = self.get_excluded_fields()

        if not rows:
            return

        if not transaction_count:
            transaction_count = len(rows)

        for index in range(0, len(rows), transaction_count):
            if conflict_fields:
                self.insert_many(rows[index:index + transaction_count]).on_conflict(
                    action=None,
                    conflict_target=conflict_fields,
                    update=update_fields,
                ).execute()
            else:
                self.insert_many(rows[index:index + transaction_count]).execute()

    def save_or_update(self, row):
        conflict_fields = self.get_model_indexes()
        row = self.match_schema(row)
        update_data = self.get_update_data(dict(row))

        if conflict_fields:
            self.insert(**row).on_conflict(
                action=None if update_data else 'IGNORE',
                conflict_target=conflict_fields,
                update=update_data,
            ).execute()
        else:
            self.insert(**row).execute()

    def match_schema(self, row: dict):
        result = {}
        schema = self.get_schema()

        for key in schema:
            if key in row:
                result[key] = row[key]

        return result

    def get_update_data(self, row):
        for val in self.get_model_indexes():
            if row.get(val):
                del row[val]

        return row

    def get_excluded_fields(self):
        fields = self.get_model_fields()
        indexes = self.get_model_indexes()
        result = {}

        fields_set = set(fields.keys())
        indexes_set = set(indexes)

        fields_without_indexes = list(fields_set - indexes_set)

        for field in fields_without_indexes:
            if isinstance(fields[field], peewee.ForeignKeyField):
                field = fields[field].object_id_name

            result[field] = getattr(EXCLUDED, field)

        return result

    # Get model fields list
    def get_schema(self):
        schema = list(self._meta.fields)

        return schema

    def get_model_indexes(self):
        indexes = list(self._meta.indexes)

        return indexes[0][0] if indexes else []

    def get_model_fields(self):
        fields = self._meta.fields

        return fields
