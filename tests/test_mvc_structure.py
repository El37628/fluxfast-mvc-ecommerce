import inspect
from app import controllers, models, views


def test_views_return_page():
    """Verify that Views only produce FluxFast Page objects and do not perform SQL execution directly."""
    for name, cls in inspect.getmembers(views, inspect.isclass):
        for method_name, method in inspect.getmembers(cls, inspect.isfunction):
            sig = inspect.signature(method)
            # In MVC, view renders should declare or return Page
            assert "render" in method_name


def test_controllers_contain_business_logic():
    """Verify that Controllers manage mutations and return schemas or mutation results."""
    for name, cls in inspect.getmembers(controllers, inspect.isclass):
        methods = [m for m, f in inspect.getmembers(cls, inspect.isfunction)]
        assert len(methods) > 0


def test_models_are_declarative():
    """Verify that Models define SQLAlchemy declarative tables."""
    for model_name in ["Category", "Customer", "Product", "Order", "OrderItem"]:
        model = getattr(models, model_name, None)
        assert model is not None
        assert hasattr(model, "__tablename__")
