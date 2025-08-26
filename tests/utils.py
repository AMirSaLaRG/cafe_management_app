from datetime import datetime, time
from typing import Dict, List, Optional, Any

def crud_cycle_test(db_handler: Any,
                    model_class: Any,
                    create_kwargs: Dict[str, Any],
                    update_kwargs: Dict[str, Any],
                    lookup_fields:Optional[list[str]] = None,
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


    if lookup_fields and lookup_values:
        assert len(lookup_fields) == len(lookup_values)
        # lookup = dict(zip(lookup_fields, lookup_values))
        lookup = {lookup_fields[lookup_fields.index(lookup_field)]: lookup_values[lookup_fields.index(lookup_field)]
                  for lookup_field in lookup_fields}

    elif lookup_fields :
        lookup_values = [getattr(obj, lookup_field) for lookup_field in lookup_fields]
        lookup = dict(zip(lookup_fields, lookup_values))
    else:
        lookup = None

    #___READ___
    get_func = getattr(db_handler, f"get_{model_name}")
    if lookup:
        fetched = get_func(**lookup)
    else:
        fetched = get_func()
    assert fetched != []
    assert len(fetched) == 1
    fetched = fetched[0]
    if lookup_fields:
        for lookup_field in lookup_fields:
            #this prevents time ranges error they may not be exact value
            if not isinstance(getattr(fetched, lookup_field), datetime) or not not isinstance(getattr(fetched, lookup_field), time):
                value_lookup_field = getattr(fetched, lookup_field)
                value_provided = lookup_values[lookup_fields.index(lookup_field)]
                if isinstance(value_provided, str):
                    value_provided = value_provided.strip().lower()
                assert value_lookup_field == value_provided

    #___UPDATE___
    for key, value in update_kwargs.items():
        setattr(fetched, key, value)
    cleaned_update_kwargs = update_kwargs.copy()
    for key, value in update_kwargs.items():
        if isinstance(value, str) and not key in ["contact_address", 'description', 'receiver_id']:
           cleaned_update_kwargs[key] = value.strip().lower()

    edit_func = getattr(db_handler, f"edit_{model_name}")
    updated = edit_func(fetched)
    assert updated is not None
    for key, value in cleaned_update_kwargs.items():
        a = getattr(updated, key)
        b = value
        assert getattr(updated, key) == value

    #___DELETE___
    delete_func = getattr(db_handler, f"delete_{model_name}")
    deleted = delete_func(updated)
    assert deleted is True

    if lookup:
        gone = get_func(**lookup)
    else:
        gone = get_func()
    assert gone == []

