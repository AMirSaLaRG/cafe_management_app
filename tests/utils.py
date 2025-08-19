from typing import Dict, List, Optional, Any

def crud_cycle_test(db_handler: Any,
                    model_class: Any,
                    create_kwargs: Dict[str, Any],
                    update_kwargs: Dict[str, Any],
                    lookup_fields:List[str],
                    lookup_values:Optional[List[Any]]=None) -> None:
    """
    Generic CRUD cycle test for any SQLAlchemy model handler by DbHandler
    :param db_handler: An instance of DDbHandler (with session + CRUD method)
    :param model_class: The SQLAlchemy model class to test
    :param create_kwargs: Dict of kwargs to pass to create new record
    :param update_kwargs: Dict of kwargs to pass to update existing record
    :param lookup_fields: Requirement list of names to fetch record
    :param lookup_values: Values of used for lookup (default: None -> uses objects id)
    """

    model_name = model_class.__name__.lower()

    #___CREATE___
    add_func = getattr(db_handler, f'add_{model_name}')
    obj = add_func(**create_kwargs)
    assert obj is not None

    if lookup_values is None:
        lookup_values = [getattr(obj, lookup_field) for lookup_field in lookup_fields]

    lookup = {lookup_fields[lookup_fields.index(lookup_field)]: lookup_values[lookup_fields.index(lookup_field)] for lookup_field in lookup_fields}
    #___READ___
    get_func = getattr(db_handler, f"get_{model_name}")
    fetched = get_func(**lookup)
    assert fetched is not None
    for lookup_field in lookup_fields:
        assert getattr(fetched, lookup_field) == lookup_values[lookup_fields.index(lookup_field)]

    #___UPDATE___
    for key, value in update_kwargs.items():
        setattr(fetched, key, value)

    edit_func = getattr(db_handler, f"edit_{model_name}")
    updated = edit_func(fetched)
    assert updated is not None
    for key, value in update_kwargs.items():
        assert getattr(updated, key) == value

    #___DELETE___
    delete_func = getattr(db_handler, f"delete_{model_name}")
    deleted = delete_func(fetched)
    assert deleted is True

    gone = get_func(**lookup)
    assert gone is None

