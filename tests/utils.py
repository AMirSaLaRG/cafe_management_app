def crud_cycle_test(db_handler, model_class, create_kwargs, update_kwargs, lookup_field='id', lookup_value=None):
    """
    Generic CRUD cycle test for any SQLAlchemy model handler by DbHandler
    :param db_handler: An instance of DDbHandler (with session + CRUD method)
    :param model_class: The SQLAlchemy model class to test
    :param create_kwargs: Dict of kwargs to pass to create new record
    :param update_kwargs: Dict of kwargs to pass to update existing record
    :param lookup_field: Field name used to fetch the record (default: "id")
    :param lookup_value: Value used for lookup (default: None -> uses objects id)
    """

    model_name = model_class.__name__.lower()

    #___CREATE___
    add_func = getattr(db_handler, f'add_{model_name}')
    obj = add_func(**create_kwargs)
    assert obj is not None
    assert getattr(obj, "id") is not None

    if lookup_value is None:
        lookup_value = getattr(obj, lookup_field)

    #___READ___
    get_func = getattr(db_handler, f"get_{model_name}")
    fetched = get_func(create_kwargs.get("name", lookup_value))
    assert fetched is not None
    assert getattr(fetched, lookup_field) == lookup_value

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
    deleted = delete_func(updated.id)
    assert deleted is True

    gone = get_func(create_kwargs.get("name", lookup_value))
    assert gone is None

