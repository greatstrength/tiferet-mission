"""tiferet_mission Mapper Test Settings

Vendored from tiferet.mappers.tests.settings until the framework publishes
test harness modules in its distribution package.
"""

# *** imports

# ** infra
import pytest

# ** app
from tiferet.assets.exceptions import TiferetError
from tiferet.mappers import Aggregate, TransferObject

# *** classes

# ** class: MapperAssertions
class MapperAssertions:
    '''
    Internal mixin providing shared assertion helpers for mapper tests.
    '''

    # * attribute: equality_fields
    equality_fields: list = []

    # * attribute: field_normalizers
    field_normalizers: dict = {}

    # * method: assert_model_matches
    def assert_model_matches(
        self,
        model,
        sample: dict,
        equality_fields: list = None,
        field_normalizers: dict = None,
    ):
        '''
        Compare model attributes against a sample data dict using configured fields and normalizers.

        :param model: The model instance to check.
        :param sample: The expected values dict.
        :type sample: dict
        :param equality_fields: Fields to compare (defaults to self.equality_fields).
        :type equality_fields: list
        :param field_normalizers: Per-field normalizers (defaults to self.field_normalizers).
        :type field_normalizers: dict
        '''

        # Use defaults from the class if not provided.
        equality_fields = equality_fields or self.equality_fields
        field_normalizers = field_normalizers or self.field_normalizers

        # Compare each field.
        for field in equality_fields:
            if field not in sample:
                continue

            expected = sample[field]
            actual = getattr(model, field, None)

            normalizer = field_normalizers.get(field)
            if normalizer:
                expected = normalizer(expected)
                actual = normalizer(actual)

            assert actual == expected, (
                f"Mismatch on field '{field}':\n"
                f"  expected: {expected!r}\n"
                f"  actual:   {actual!r}"
            )


# ** class: AggregateTestBase
class AggregateTestBase(MapperAssertions):
    '''
    Base class for testing Aggregate components.

    Subclasses define:
    - aggregate_cls          — the Aggregate class under test
    - sample_data            — aggregate-format sample data
    - equality_fields        — fields to compare
    - field_normalizers      — optional per-field normalizers
    - set_attribute_params   — tuples of (attr, value, expect_error_code | None)
    '''

    # * attribute: aggregate_cls
    aggregate_cls = None

    # * attribute: sample_data
    sample_data: dict = {}

    # * attribute: set_attribute_params
    set_attribute_params: list = []

    # * method: make_aggregate
    def make_aggregate(self, data: dict = None):
        '''
        Create an aggregate from data. Override for custom constructor signatures.

        :param data: The data to create from (defaults to self.sample_data).
        :type data: dict
        :return: A new aggregate instance.
        '''

        # Create an aggregate using the standard Pydantic constructor.
        return self.aggregate_cls(**(data or self.sample_data))

    # * fixture: aggregate
    @pytest.fixture
    def aggregate(self):
        '''
        Fixture providing an aggregate instance from sample_data.
        '''

        # Skip if no aggregate class is defined.
        if not self.aggregate_cls:
            pytest.skip("aggregate_cls not defined")

        # Create and return the aggregate.
        return self.make_aggregate()

    # * method: test_new
    def test_new(self, aggregate):
        '''
        Verify aggregate instantiation and field values match sample_data.
        '''

        # Assert the aggregate is the correct type.
        assert isinstance(aggregate, self.aggregate_cls)

        # Assert the aggregate fields match the sample data.
        self.assert_model_matches(aggregate, self.sample_data)

    # * method: test_set_attribute
    def test_set_attribute(self, aggregate, attr, value, expect_error_code):
        '''
        Parametrized test for set_attribute (valid and invalid).
        Parametrization is handled by conftest.pytest_generate_tests.
        '''

        # If an error is expected, verify the correct error code is raised.
        if expect_error_code:
            with pytest.raises(TiferetError) as exc_info:
                aggregate.set_attribute(attr, value)
            assert exc_info.value.error_code == expect_error_code

        # Otherwise verify the attribute was updated.
        else:
            aggregate.set_attribute(attr, value)
            assert getattr(aggregate, attr) == value


# ** class: TransferObjectTestBase
class TransferObjectTestBase(MapperAssertions):
    '''
    Base class for testing TransferObject components.

    Subclasses define:
    - transfer_cls            — the TransferObject class under test
    - aggregate_cls           — the target Aggregate class
    - sample_data             — sample data for construction
    - aggregate_sample_data   — aggregate-format expected data
    - equality_fields         — fields to compare on mapped results
    - field_normalizers       — optional per-field normalizers
    - map_kwargs              — extra kwargs to pass to .map()
    '''

    # * attribute: transfer_cls
    transfer_cls = None

    # * attribute: aggregate_cls
    aggregate_cls = None

    # * attribute: sample_data
    sample_data: dict = {}

    # * attribute: aggregate_sample_data
    aggregate_sample_data: dict = {}

    # * attribute: map_kwargs
    map_kwargs: dict = {}

    # * method: make_aggregate
    def make_aggregate(self, data: dict = None):
        '''
        Create an aggregate for from_model / round_trip tests.
        Override for custom constructor signatures.

        :param data: The data to create from (defaults to self.aggregate_sample_data).
        :type data: dict
        :return: A new aggregate instance.
        '''

        # Create an aggregate using the standard Pydantic constructor.
        return self.aggregate_cls(**(data or self.aggregate_sample_data))

    # * fixture: aggregate
    @pytest.fixture
    def aggregate(self):
        '''
        Fixture providing an aggregate instance from aggregate_sample_data.
        '''

        # Skip if no aggregate class is defined.
        if not self.aggregate_cls:
            pytest.skip("aggregate_cls not defined")

        # Create and return the aggregate.
        return self.make_aggregate()

    # * method: test_map
    def test_map(self):
        '''
        Verify TransferObject construction -> map() produces a valid aggregate.
        '''

        # Skip if no transfer class is defined.
        if not self.transfer_cls:
            pytest.skip("transfer_cls not defined")

        # Create a transfer object from sample data.
        obj = self.transfer_cls.model_validate(self.sample_data)

        # Map to an aggregate.
        mapped = obj.map(**self.map_kwargs)

        # Assert the mapped aggregate is the correct type and matches expected data.
        assert isinstance(mapped, self.aggregate_cls)
        self.assert_model_matches(mapped, self.aggregate_sample_data)

    # * method: test_from_model
    def test_from_model(self, aggregate):
        '''
        Verify aggregate -> TransferObject conversion.
        '''

        # Skip if no transfer class is defined.
        if not self.transfer_cls:
            pytest.skip("transfer_cls not defined")

        # Convert the aggregate to a transfer object using the classmethod.
        obj = self.transfer_cls.from_model(aggregate)

        # Assert the result is the correct type.
        assert isinstance(obj, self.transfer_cls)

    # * method: test_round_trip
    def test_round_trip(self, aggregate):
        '''
        Verify aggregate -> TransferObject -> aggregate round-trip.
        '''

        # Skip if no transfer class is defined.
        if not self.transfer_cls:
            pytest.skip("transfer_cls not defined")

        # Convert aggregate to transfer object and back.
        obj = self.transfer_cls.from_model(aggregate)
        round_tripped = obj.map(**self.map_kwargs)

        # Assert the round-tripped aggregate matches expected data.
        assert isinstance(round_tripped, self.aggregate_cls)
        self.assert_model_matches(round_tripped, self.aggregate_sample_data)
