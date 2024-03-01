import re
from typing import Any, get_args

import pydantic
import pytest

from pydantic_partial import PartialModelMixin
from pydantic_partial._compat import PYDANTIC_V1, PYDANTIC_V2

if PYDANTIC_V2:
    from pydantic import ConfigDict

if PYDANTIC_V1:
    def _field_is_required(model: pydantic.BaseModel, field_name: str) -> bool:
        """Check if a field is required on a pydantic V1 model."""
        return model.__fields__[field_name].required

    def _get_subtype(model:pydantic.BaseModel,field_name: str)-> pydantic.BaseModel:
        return model.__fields__[field_name].type_

    def _get_alias(model:pydantic.BaseModel,field_name: str)-> str:
        return model.__fields__[field_name].field_info.alias

    def _get_title(model:pydantic.BaseModel,field_name: str)-> str:
        return model.__fields__[field_name].field_info.title

    def _get_extra(model:pydantic.BaseModel,field_name: str)-> dict[str,Any]:
        return model.__fields__[field_name].field_info.extra

elif PYDANTIC_V2:
    def _field_is_required(model: pydantic.BaseModel, field_name: str) -> bool:
        """Check if a field is required on a pydantic V2 model."""
        return model.model_fields[field_name].is_required()

    def _get_subtype(model:pydantic.BaseModel,field_name: str)->pydantic.BaseModel:
        try:
            return get_args(get_args(model.model_fields[field_name].annotation)[0])[0]
        except IndexError:
            return get_args(model.model_fields[field_name].annotation)[0]

    def _get_alias(model:pydantic.BaseModel,field_name: str)-> str:
        return model.model_fields[field_name].alias

    def _get_title(model:pydantic.BaseModel,field_name: str)-> str:
        return model.model_fields[field_name].title

    def _get_extra(model:pydantic.BaseModel,field_name: str)-> dict[str,Any]:
        return model.model_fields[field_name].json_schema_extra

else:
    raise DeprecationWarning("Pydantic has to be in version 1 or 2.")


class Something(PartialModelMixin, pydantic.BaseModel):
    if PYDANTIC_V2:
        name: str = pydantic.Field(
            ..., alias="test_name", title="TEST Name",
            json_schema_extra={"something_else": True},
        )
    if PYDANTIC_V1:
        name: str = pydantic.Field(
            ..., alias="test_name", title="TEST Name",
            something_else=True,
        )  # type: ignore
    age: int
    already_optional: None = None

    if PYDANTIC_V2:
        model_config = ConfigDict(populate_by_name=True)
    if PYDANTIC_V1:
        class Config:
            allow_population_by_field_name = True


class SomethingList(PartialModelMixin, pydantic.BaseModel):
    items: list[Something]


@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v1 did change fields handling")
def test_setup_is_sane_v2():
    assert Something.model_fields["name"].is_required() is True
    assert Something.model_fields["age"].is_required() is True
    assert SomethingList.model_fields["items"].is_required() is True


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_setup_is_sane_v1():
    assert Something.__fields__["name"].required is True
    assert Something.__fields__["age"].required is True
    assert SomethingList.__fields__["items"].required is True

def test_setup_is_sane():
    assert _field_is_required(Something,"name") is True
    assert _field_is_required(Something,"age")  is True
    assert _field_is_required(SomethingList,"items")  is True

@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v2 did change fields handling")
def test_partial_will_make_all_fields_optional_v2():
    SomethingPartial = Something.model_as_partial()

    assert SomethingPartial.model_fields["name"].is_required() is False
    assert SomethingPartial.model_fields["age"].is_required() is False
    SomethingPartial()


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_partial_will_make_all_fields_optional_v1():
    SomethingPartial = Something.model_as_partial()

    assert SomethingPartial.__fields__["name"].required is False
    assert SomethingPartial.__fields__["age"].required is False
    SomethingPartial()

def test_partial_will_make_all_fields_optional():
    SomethingPartial = Something.model_as_partial()

    assert _field_is_required(SomethingPartial,"name") is False
    assert _field_is_required(SomethingPartial,"age")  is False
    SomethingPartial()

@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v2 did change fields handling")
def test_partial_will_keep_original_field_options_v2():
    SomethingPartial = Something.model_as_partial()

    assert SomethingPartial.model_fields["name"].alias == "test_name"
    assert SomethingPartial.model_fields["name"].title == "TEST Name"
    assert (
        SomethingPartial.model_fields["name"].json_schema_extra["something_else"]
        is True
    )


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_partial_will_keep_original_field_options_v1():
    SomethingPartial = Something.model_as_partial()

    assert SomethingPartial.__fields__["name"].field_info.alias == "test_name"
    assert SomethingPartial.__fields__["name"].field_info.title == "TEST Name"
    assert (
        SomethingPartial.__fields__["name"].field_info.extra["something_else"]
        is True
    )

def test_partial_will_keep_original_field_options():
    SomethingPartial = Something.model_as_partial()

    assert _get_alias(SomethingPartial,"name") == "test_name"
    assert _get_title(SomethingPartial,"name") == "TEST Name"
    assert _get_extra(SomethingPartial,"name")["something_else"] is True

@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v2 did change fields handling")
def test_partial_allows_to_only_change_certain_fields_v2():
    SomethingNamePartial = Something.model_as_partial("name")

    assert SomethingNamePartial.model_fields["name"].is_required() is False
    assert SomethingNamePartial.model_fields["age"].is_required() is True
    SomethingNamePartial(age=1)
    with pytest.raises(pydantic.ValidationError):
        SomethingNamePartial(name="test")

    SomethingAgePartial = Something.model_as_partial("age")

    assert SomethingAgePartial.model_fields["name"].is_required() is True
    assert SomethingAgePartial.model_fields["age"].is_required() is False
    SomethingAgePartial(name="test")
    with pytest.raises(pydantic.ValidationError):
        SomethingAgePartial(age=1)

    SomethingPartial = Something.model_as_partial("name", "age")

    assert SomethingPartial.model_fields["name"].is_required() is False
    assert SomethingPartial.model_fields["age"].is_required() is False
    SomethingPartial()


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_partial_allows_to_only_change_certain_fields_v1():
    SomethingNamePartial = Something.model_as_partial("name")

    assert SomethingNamePartial.__fields__["name"].required is False
    assert SomethingNamePartial.__fields__["age"].required is True
    SomethingNamePartial(age=1)
    with pytest.raises(pydantic.ValidationError):
        SomethingNamePartial(name="test")

    SomethingAgePartial = Something.model_as_partial("age")

    assert SomethingAgePartial.__fields__["name"].required is True
    assert SomethingAgePartial.__fields__["age"].required is False
    SomethingAgePartial(name="test")
    with pytest.raises(pydantic.ValidationError):
        SomethingAgePartial(age=1)

    SomethingPartial = Something.model_as_partial("name", "age")

    assert SomethingPartial.__fields__["name"].required is False
    assert SomethingPartial.__fields__["age"].required is False
    SomethingPartial()



def test_partial_allows_to_only_change_certain_fields():
    SomethingNamePartial = Something.model_as_partial("name")

    assert _field_is_required(SomethingNamePartial,"name") is False
    assert _field_is_required(SomethingNamePartial,"age") is True

    SomethingNamePartial(age=1)
    with pytest.raises(pydantic.ValidationError):
        SomethingNamePartial(name="test")

    SomethingAgePartial = Something.model_as_partial("age")

    assert _field_is_required(SomethingAgePartial,"name") is True
    assert _field_is_required(SomethingAgePartial,"age") is False
    SomethingAgePartial(name="test")
    with pytest.raises(pydantic.ValidationError):
        SomethingAgePartial(age=1)

    SomethingPartial = Something.model_as_partial("name", "age")

    assert _field_is_required(SomethingPartial,"name") is False
    assert _field_is_required(SomethingPartial,"age") is False
    SomethingPartial()


@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v2 did change fields handling")
def test_partial_allows_recursive_usage_v2():
    SomethingListPartial = SomethingList.model_as_partial()

    assert SomethingListPartial.model_fields["items"].is_required() is False
    # Optional[List[...]]
    sub_type = get_args(get_args(SomethingListPartial.model_fields["items"].annotation)[0])[0]
    assert sub_type.model_fields["name"].is_required() is True
    assert sub_type.model_fields["age"].is_required() is True

    SomethingListRecursivePartial = SomethingList.model_as_partial(recursive=True)

    assert SomethingListRecursivePartial.model_fields["items"].is_required() is False
    # Optional[List[...]]
    sub_type = get_args(get_args(SomethingListRecursivePartial.model_fields["items"].annotation)[0])[0]
    assert sub_type.model_fields["name"].is_required() is False
    assert sub_type.model_fields["age"].is_required() is False


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_partial_allows_recursive_usage_v1():
    SomethingListPartial = SomethingList.model_as_partial()

    assert SomethingListPartial.__fields__["items"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is True
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is True

    SomethingListRecursivePartial = SomethingList.model_as_partial(recursive=True)

    assert SomethingListRecursivePartial.__fields__["items"].required is False
    assert SomethingListRecursivePartial.__fields__["items"].type_.__fields__["name"].required is False
    assert SomethingListRecursivePartial.__fields__["items"].type_.__fields__["age"].required is False

def test_partial_allows_recursive_usage():
    SomethingListPartial = SomethingList.model_as_partial()

    assert _field_is_required(SomethingListPartial,"items") is False
    # Optional[List[...]]
    sub_type = _get_subtype(SomethingListPartial, "items")
    assert _field_is_required(sub_type,"name") is True
    assert _field_is_required(sub_type,"age") is True

    SomethingListRecursivePartial = SomethingList.model_as_partial(recursive=True)

    assert _field_is_required(SomethingListRecursivePartial,"items") is False
    # Optional[List[...]]
    sub_type = _get_subtype(SomethingListRecursivePartial,"items")
    assert _field_is_required(sub_type,"name") is False
    assert _field_is_required(sub_type,"age") is False


@pytest.mark.skipif(PYDANTIC_V1, reason="pydantic v2 did change fields handling")
def test_partial_allows_explicit_recursive_v2():
    SomethingListPartial = SomethingList.model_as_partial("items.*")

    assert SomethingListPartial.model_fields["items"].is_required() is True
    sub_type = get_args(SomethingListPartial.model_fields["items"].annotation)[0]  # List[...]
    assert sub_type.model_fields["name"].is_required() is False
    assert sub_type.model_fields["age"].is_required() is False
    SomethingListPartial(items=[])

    SomethingListPartial = SomethingList.model_as_partial("items")

    assert SomethingListPartial.model_fields["items"].is_required() is False
    # Optional[List[...]]
    sub_type = get_args(get_args(SomethingListPartial.model_fields["items"].annotation)[0])[0]
    assert sub_type.model_fields["name"].is_required() is True
    assert sub_type.model_fields["age"].is_required() is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)

    SomethingListPartial = SomethingList.model_as_partial("items.name")

    assert SomethingListPartial.model_fields["items"].is_required() is True
    sub_type = get_args(SomethingListPartial.model_fields["items"].annotation)[0]  # List[...]
    assert sub_type.model_fields["name"].is_required() is False
    assert sub_type.model_fields["age"].is_required() is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])

    SomethingListPartial = SomethingList.model_as_partial(recursive=True)

    assert SomethingListPartial.model_fields["items"].is_required() is False
    # Optional[List[...]]
    sub_type = get_args(get_args(SomethingListPartial.model_fields["items"].annotation)[0])[0]
    assert sub_type.model_fields["name"].is_required() is False
    assert sub_type.model_fields["age"].is_required() is False
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)
    SomethingListPartial(items=[{}])

    SomethingListPartial = SomethingList.model_as_partial("items.name", recursive=True)

    assert SomethingListPartial.model_fields["items"].is_required() is True
    sub_type = get_args(SomethingListPartial.model_fields["items"].annotation)[0]  # List[...]
    assert sub_type.model_fields["name"].is_required() is False
    assert sub_type.model_fields["age"].is_required() is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])


@pytest.mark.skipif(PYDANTIC_V2, reason="pydantic v2 did change fields handling")
def test_partial_allows_explicit_recursive_v1():
    SomethingListPartial = SomethingList.model_as_partial("items.*")

    assert SomethingListPartial.__fields__["items"].required is True
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is False
    SomethingListPartial(items=[])

    SomethingListPartial = SomethingList.model_as_partial("items")

    assert SomethingListPartial.__fields__["items"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is True
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)

    SomethingListPartial = SomethingList.model_as_partial("items.name")

    assert SomethingListPartial.__fields__["items"].required is True
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])

    SomethingListPartial = SomethingList.model_as_partial(recursive=True)

    assert SomethingListPartial.__fields__["items"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is False
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)
    SomethingListPartial(items=[{}])

    SomethingListPartial = SomethingList.model_as_partial("items.name", recursive=True)

    assert SomethingListPartial.__fields__["items"].required is True
    assert SomethingListPartial.__fields__["items"].type_.__fields__["name"].required is False
    assert SomethingListPartial.__fields__["items"].type_.__fields__["age"].required is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])

def test_partial_allows_explicit_recursive():
    SomethingListPartial = SomethingList.model_as_partial("items.*")

    assert _field_is_required(SomethingListPartial,"items") is True
    sub_type = _get_subtype(SomethingListPartial,"items")  # List[...]
    assert _field_is_required(sub_type,"name") is False
    assert _field_is_required(sub_type,"age") is False
    SomethingListPartial(items=[])

    SomethingListPartial = SomethingList.model_as_partial("items")

    assert _field_is_required(SomethingListPartial,"items") is False
    # Optional[List[...]]
    sub_type = _get_subtype(SomethingListPartial,"items")
    assert _field_is_required(sub_type,"name") is True
    assert _field_is_required(sub_type,"age") is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)

    SomethingListPartial = SomethingList.model_as_partial("items.name")

    assert _field_is_required(SomethingListPartial,"items") is True
    sub_type = _get_subtype(SomethingListPartial,"items")  # List[...]
    assert _field_is_required(sub_type,"name") is False
    assert _field_is_required(sub_type,"age") is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])

    SomethingListPartial = SomethingList.model_as_partial(recursive=True)

    assert _field_is_required(SomethingListPartial,"items") is False
    # Optional[List[...]]
    sub_type = _get_subtype(SomethingListPartial,"items")
    assert _field_is_required(sub_type,"name") is False
    assert _field_is_required(sub_type,"age") is False
    SomethingListPartial(items=[])
    SomethingListPartial(items=None)
    SomethingListPartial(items=[{}])

    SomethingListPartial = SomethingList.model_as_partial("items.name", recursive=True)

    assert _field_is_required(SomethingListPartial,"items") is True
    sub_type = _get_subtype(SomethingListPartial,"items")  # List[...]
    assert _field_is_required(sub_type,"name") is False
    assert _field_is_required(sub_type,"age") is True
    SomethingListPartial(items=[])
    SomethingListPartial(items=[{"age": 1}])

def test_no_change_to_optional_fields():
    SomethingPartial = Something.model_as_partial("already_optional")

    assert SomethingPartial is Something


def test_as_partial_works_as_expected():
    with pytest.warns(DeprecationWarning):
        assert Something.model_as_partial() is Something.as_partial()
