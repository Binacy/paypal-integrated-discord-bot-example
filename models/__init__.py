from pypika.terms import Function
from tortoise.expressions import F
from tortoise.fields.base import Field
from tortoise.validators import Validator
from tortoise.exceptions import ValidationError
from tortoise import fields, models
from enum import Enum


class ArrayAppend(Function):
    def __init__(self, field: str, value) -> None:
        if isinstance(value, Enum):
            value = value.value

        super().__init__("ARRAY_APPEND", F(field), str(value))


class ArrayRemove(Function):
    def __init__(self, field: str, value) -> None:
        if isinstance(value, Enum):
            value = value.value

        super().__init__("ARRAY_REMOVE", F(field), str(value))


class ArrayField(Field, list):
    def __init__(self, field: Field, **kwargs) -> None:
        super().__init__(**kwargs)
        self.sub_field = field
        self.SQL_TYPE = "%s[]" % field.SQL_TYPE

    def to_python_value(self, value):
        return list(map(self.sub_field.to_python_value, value))

    def to_db_value(self, value, instance):
        return [self.sub_field.to_db_value(val, instance) for val in value]


class ValueRangeValidator(Validator):
    """
    A validator to validate whether the given value is in given range or not.
    """

    def __init__(self, _range: range):
        self._range = _range

    def __call__(self, value: int):
        if not value in self._range:
            raise ValidationError(
                f"The value must be a number between `{self._range.start}` and `{self._range.stop}`."
            )


#####################################################################################################################################


class Transactions(models.Model):
    class Meta:
        table = "transactions"

    id = fields.TextField(pk=True)
    payapl_id = fields.TextField()
    user_id = fields.BigIntField()
    paid = fields.BooleanField(default=False)
    amount = fields.IntField()
    product_id = fields.IntField()
    product_name = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)


class Products(models.Model):
    class Meta:
        table = "products"

    id = fields.IntField(pk=True, generated=True)
    name = fields.TextField()
    price = fields.IntField()
    discount = fields.IntField(default=0)
    description = fields.TextField()
    role = fields.BigIntField(null=True)
    stock = fields.IntField(default=10)
    user = fields.BigIntField(null=True)
    image = fields.TextField(null=True)
    example_image = fields.TextField(null=True)
    temp = fields.BooleanField(default=False)


class RoleDiscounts(models.Model):
    class Meta:
        table = "role_discounts"

    role_id = fields.BigIntField(pk=True)
    discount = fields.IntField(default=0)


class Role_Products(models.Model):
    class Meta:
        table = "role_products"

    role_id = fields.BigIntField(pk=True)
    role_name = fields.TextField()
    price = fields.IntField()
    description = fields.TextField()
    discount = fields.IntField(default=0)
    stock = fields.IntField(default=10)


class Role_Transactions(models.Model):
    class Meta:
        table = "role_transactions"

    id = fields.TextField(pk=True)
    payapl_id = fields.TextField()
    user_id = fields.BigIntField()
    paid = fields.BooleanField(default=False)
    amount = fields.IntField()
    role_id = fields.BigIntField()
    role_name = fields.TextField()
    timestamp = fields.DatetimeField(auto_now_add=True)
